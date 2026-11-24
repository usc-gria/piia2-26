---
description: La interfaz es una app de Streamlit que solo contiene la presentación; la lógica vive en src/.
state: Aceptado
---

# ADR — Interfaz en Streamlit

## Decisión
La herramienta interactiva es una app de Streamlit (`src/app.py`). La app solo contiene la interfaz: carga y visor de imágenes, edición de resultados y exportación. La ingesta, las llamadas al modelo y la validación viven en `src/`, para que el script de evaluación use exactamente el mismo código.

## Motivación
SDG propuso Streamlit en la reunión 1 y en la planificación. Permite construir la demo en Python, sin un frontend aparte, y trae lo que necesita la planificación: subida de ficheros, visor de imágenes, tablas editables y `st.download_button` para exportar.

## Alternativas consideradas
- Gradio. Rechazada: cubre la subida de imágenes y las tablas, pero está orientado a demos de una función con entrada y salida. Las pestañas, el estado por documento durante la sesión y la revalidación al editar habría que montarlos a mano con `gr.Blocks` y `gr.State`, mientras que Streamlit los trae con `st.tabs`, `st.session_state` y el `on_change` de `st.data_editor`. Además, SDG propuso Streamlit.
- Frontend web propio con una API aparte. Rechazada: cuesta semanas que no aportan al objetivo, que es demostrar el procesamiento de documentos.

## Referencias
- https://streamlit.io/
- Acta de la reunión 1 con SDG (08-10-2026, `docs/Reuniones/Reunión1.docx`, no publicada). Su primera línea propone Streamlit, con el enlace a su web.
- Acta del 22-10-2026: «Poner las cosas en formato tabla» y «Hacer un reporte de métricas de todos los documentos en otra pestaña». De ahí salen `st.data_editor` y la pestaña «Reporte de métricas».
- Planificación acordada con SDG (`docs/Planificación.pdf`, no publicada). En la semana 2: «Crear la interfaz gráfica principal en Streamlit (app.py)». En la semana 4: «Exportación multiformato: añadir botones para descargar la información procesada en Excel (.xlsx), CSV y JSON (st.download_button)».
- Componentes que usa la app, con su documentación oficial:

  | Necesidad | Componente | Documentación |
  |---|---|---|
  | Subir imágenes | `st.file_uploader` | https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader |
  | Ver el documento | `st.image` | https://docs.streamlit.io/develop/api-reference/media/st.image |
  | Editar entidades | `st.data_editor` | https://docs.streamlit.io/develop/api-reference/data/st.data_editor |
  | Exportar | `st.download_button` | https://docs.streamlit.io/develop/api-reference/widgets/st.download_button |
  | Preguntas | `st.chat_input` | https://docs.streamlit.io/develop/api-reference/chat/st.chat_input |
  | Resultados por documento | `st.session_state` | https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state |
  | Un solo cliente de Groq | `st.cache_resource` | https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_resource |

- Boceto inicial de la interfaz (`docs/Diseño Interfaz.excalidraw`, no publicado): lista de documentos, imagen, tipo de documento («Clasificación»), JSON de salida del modelo, un campo de texto para preguntas, un botón «Guardar» y una pestaña de métricas.

Patrón que sigue `src/app.py`: la app solo llama a funciones de `src/` y pinta el resultado. Streamlit vuelve a ejecutar el script entero con cada interacción, así que lo caro (cliente, dataset) se guarda en caché y los resultados en `st.session_state`.

```python
@st.cache_resource
def _model_client() -> ModelClient:
    return ModelClient.from_env()


resultado = procesar_documento(_model_client(), imagen)  # lógica en src/
st.session_state["document_results"][clave] = resultado
editado = st.data_editor(entities_to_tables(tipo, entidades)[TABLE_FIELDS])
st.download_button("JSON", to_json_bytes(...), file_name="resultado.json")
```

Se arranca con `streamlit run src/app.py`.
