import json

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode
from PIL import Image

MAP_PATH = "data/small.png"
ANNOTATIONS_PATH = "data/polygons.json"
DESCRIPTION_PATH = "data/description.json"
MAP = Image.open(MAP_PATH)

with open(ANNOTATIONS_PATH, "r") as f:
    ANNOTATIONS = json.load(f)

for idx, ann in ANNOTATIONS.items():
    ann["ID"] = idx

ANNOTATIONS = list(ANNOTATIONS.values())
ANNOTATIONS_COLS = ["comment", "label", "desc", "ID", "points"]
ANNOTATIONS_DF = pd.DataFrame(ANNOTATIONS)[ANNOTATIONS_COLS]
ANNOTATIONS_DF.rename(columns={"comment": "Numer", "label": "Typ", "desc": "Opis"}, inplace=True)
ANNOTATIONS_DF = ANNOTATIONS_DF.set_index("Numer")

with open(DESCRIPTION_PATH) as f:
    DESCRIPTION = json.load(f)

split_ids = []
for desc in DESCRIPTION:
    if isinstance(desc["Nr bieżący"], str):
        ids = desc["Nr bieżący"].split(",")
    else:
        ids = [str(desc["Nr bieżący"])]
    for id in ids:
        temp = dict(**desc)
        temp["Nr bieżący"] = id.strip()
        split_ids.append(temp)

DESCRIPTION_DF = pd.DataFrame(split_ids)
DESCRIPTION_DF.rename(columns={"Nr bieżący": "Numer"}, inplace=True)
DESCRIPTION_DF.set_index("Numer", inplace=True)
num_cols = ["Szerokość pręty", "Szerokość stopy", "Powierzchnia morgi", "Powierzchnia pręty", "Powierzchnia stopy"]
DESCRIPTION_DF[num_cols] = DESCRIPTION_DF[num_cols].replace([np.inf, -np.inf], 0)
DESCRIPTION_DF[num_cols] = DESCRIPTION_DF[num_cols].fillna(0)
DESCRIPTION_DF[num_cols] = DESCRIPTION_DF[num_cols].astype(int)

ANNOTATIONS_DF = ANNOTATIONS_DF.merge(DESCRIPTION_DF, on="Numer", how="left")
ANNOTATIONS_DF[num_cols] = ANNOTATIONS_DF[num_cols].replace([np.inf, -np.inf], 0)
ANNOTATIONS_DF[num_cols] = ANNOTATIONS_DF[num_cols].fillna(0)
ANNOTATIONS_DF[num_cols] = ANNOTATIONS_DF[num_cols].astype(int)



def create_annotated_image_plot(image: Image.Image, annotations: pd.DataFrame):
    w, h = image.width, image.height
    fig = px.imshow(image,
                    width=1800, height=1000,
                    binary_string=True, binary_format="jpg", binary_compression_level=3)
    fig.update_traces(hoverinfo='skip', hovertemplate=None)

    # For each label, add a filled scatter trace for its contour,
    # and display the properties of the label in the hover of this trace.
    w, h = image.width, image.height
    for idx, row in annotations.iterrows():
        points = np.array(row["points"])
        points = (points / 100) * np.array([w, h])
        x, y = points[:, 0], points[:, 1]
        hoverinfo = ''
        for prop_name in ANNOTATIONS_DF.columns:
            if prop_name in ["ID", "points"] or not row[prop_name] or pd.isna(row[prop_name]):
                continue

            hoverinfo += f'<b>{prop_name}: {row[prop_name]}</b><br>'
        fig.add_trace(go.Scatter(
            x=x, y=y, name=hoverinfo,
            mode='lines', fill='toself', showlegend=False,
            opacity=0,
            hoveron='fills', hoverinfo="text"
            )
        )

    fig.update_layout(
        coloraxis_showscale=False,
        hoverlabel=dict(bgcolor="white"),
        margin=dict(l=0, r=0, t=0, b=0)
    )
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)
    return fig


st.set_page_config(layout="wide")

map_tab, table_tab = st.tabs(["Mapa", "Tabela"])

with map_tab:
    st.title('Mapa Wąwolnicy z roku 1820')

    st.plotly_chart(create_annotated_image_plot(MAP, ANNOTATIONS_DF), use_container_width=True)

with table_tab:
    opts_builder = GridOptionsBuilder.from_dataframe(ANNOTATIONS_DF)
    opts_builder.configure_column("ID", initialHide=True)
    opts_builder.configure_column("points", initialHide=True)
    opts_builder.configure_column("Budynek", "Budynek")
    opts_builder.configure_column("Typ", "Typ")
    opts_builder.configure_column("Opis", "Opis")
    opts_builder.configure_selection("single", use_checkbox=True)
    opts_builder.configure_pagination(enabled=True,
                                        paginationAutoPageSize=False,
                                        paginationPageSize=50)
    opts_builder.configure_columns()
    opts = opts_builder.build()
    table = AgGrid(DESCRIPTION_DF, opts,
                    columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS
                    fit_columns_on_grid_load=True,
                    reload_data=True)

    # col1, col2 = st.columns(2)
    # with col1:
    #     opts_builder = GridOptionsBuilder.from_dataframe(ANNOTATIONS_DF)
    #     opts_builder.configure_column("ID", initialHide=True)
    #     opts_builder.configure_column("points", initialHide=True)
    #     opts_builder.configure_column("Budynek", "Budynek")
    #     opts_builder.configure_column("Typ", "Typ")
    #     opts_builder.configure_column("Opis", "Opis")
    #     opts_builder.configure_selection("single", use_checkbox=True)
    #     opts_builder.configure_pagination(enabled=True,
    #                                       paginationAutoPageSize=False,
    #                                       paginationPageSize=50)
    #     opts = opts_builder.build()
    #     table = AgGrid(DESCRIPTION_DF, opts,
    #                    columns_auto_size_mode="fit_columns",
    #                    fit_columns_on_grid_load=True,
    #                    reload_data=True)

    # with col2:
    #     with st.empty():
    #         selected_rows = table["selected_rows"]
    #         if False and len(selected_rows) == 1: # TODO: currently disabled
    #             selected_row = selected_rows[0]
    #             with st.form(key='form'):
    #                 st.title("Edycja")
    #                 st.text_input("Budynek:", value=selected_row["Budynek"], key="number")
    #                 st.text_input("Typ:", value=selected_row["Typ"], key="type")
    #                 st.text_area("Opis:", value=selected_row["Opis"], key="desc",)

    #                 def modify_row():
    #                     ANNOTATIONS_DF.loc[ANNOTATIONS_DF["ID"] == selected_row["ID"], "Budynek"] = st.session_state.number
    #                     ANNOTATIONS_DF.loc[ANNOTATIONS_DF["ID"] == selected_row["ID"], "Typ"] = st.session_state.type
    #                     ANNOTATIONS_DF.loc[ANNOTATIONS_DF["ID"] == selected_row["ID"], "Opis"] = st.session_state.desc
    #                     ANNOTATIONS_DF.to_json(ANNOTATIONS_PATH, orient="index")

    #                 st.form_submit_button(label='Zapisz', on_click=modify_row)
    #         else:
    #             st.title("Wybierz wiersz do edycji - aktualnie nie działa")
