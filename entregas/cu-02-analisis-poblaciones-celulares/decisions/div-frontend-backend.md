# ADR: Frontend web + backend FastAPI local dentro de una ventana de escritorio

## Decisión
La aplicación se divide en un frontend web (React) y un backend Python con **FastAPI** que corre en local (solo en `127.0.0.1`). Una ventana **pywebview** muestra el frontend como una app de escritorio. Ambos se comunican por HTTP/JSON, y los modelos **Pydantic** definen el contrato.

## Motivación
- **Por qué no solo frontend:** las llamadas al LLM, el bucle de verificación-corrección, la lectura de ficheros, SQLite y el almacenamiento de API keys son más sencillos y seguros en Python.
- **Por qué no solo Python:** la interfaz exige gráficos SVG propios, navegación por teclado, accesibilidad (Lighthouse ≥ 90) y actualizar tablas y mapas de calor en menos de 300 ms con 10 tipos celulares × 50 rutas. Eso se resuelve mejor con una SPA web.
- **Por qué FastAPI:** documentación automática (OpenAPI), validación de entradas y salidas con tipos estrictos mediante Pydantic, y poco código.
- El frontend sigue pudiendo abrirse en un navegador normal, lo que facilita desarrollarlo y probarlo por separado.

## Alternativas
- **API de pywebview (`js_api`):** no añade dependencias, pero no tiene validación integrada, escala peor al crecer los endpoints, no genera documentación y complica la subida de ficheros.
- **Frameworks Python para interfaces (Streamlit, Dash, Gradio):** rápidos de hacer, pero no permiten el control de SVG, teclado y accesibilidad que exige la spec del frontend.
- **Electron o Tauri:** añaden otro runtime (Node o Rust) y la lógica Python seguiría necesitando un proceso aparte.
- **Django:** incluye ORM, plantillas y autenticación que no usamos; es demasiado pesado para una API local.
- **Flask:** es simple, pero no trae validación ni documentación automática; habría que añadirlas con extensiones.

## Consecuencias
- Mantener un contrato HTTP entre frontend y backend exige cuidar los modelos de respuesta.

## Referencias
- FastAPI: [Tutorial](https://fastapi.tiangolo.com/tutorial/), [FastAPI OpenAPI](https://fastapi.tiangolo.com/reference/openapi/)
- Pydantic: https://pydantic.dev/docs/validation/latest/get-started/
- pywebview (`js_api`): https://pywebview.flowrl.com/guide/interdomain.html