import flet as ft
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
import tempfile
import os
import threading
import webbrowser
from datetime import datetime

def main(page: ft.Page):
    page.title = "🧮 Calculadora de Ecuaciones Diferenciales"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 700
    page.window_height = 800
    page.padding = 20
    page.scroll = ft.ScrollMode.ADAPTIVE
    
    # Variables para almacenar la solución
    current_solution = None
    solution_params = {"t0": 0, "tf": 0, "equation": ""}
    
    # Función para crear un estilo consistente para los botones
    def create_button_style(color=ft.colors.BLUE_100):
        return ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=12,
            bgcolor=color
        )

    # Función para manejar los errores de manera más amigable
    def show_error(message):
        resultado_text.value = f"❌ Error: {message}"
        resultado_text.color = ft.colors.RED_600
        page.update()

    # Función para mostrar el resultado exitoso
    def show_success(message):
        resultado_text.value = message
        resultado_text.color = ft.colors.GREEN_700
        page.update()
    
    # Textos informativos
    header = ft.Text(
        "📘 Calculadora de Ecuaciones Diferenciales", 
        size=26, 
        weight=ft.FontWeight.BOLD, 
        text_align=ft.TextAlign.CENTER
    )
    
    instructions = ft.Container(
        content=ft.Text(
            "📝 Escribe tu ecuación usando los botones:\n"
            "➤ Puedes usar +, -, *, /, ^ (potencia).\n"
            "➤ Funciones válidas: sin(t), cos(t), exp(t), log(t).\n"
            "✅ Ejemplo: y - t^2 + 1", 
            size=14, 
            italic=True, 
            color=ft.colors.BLUE_GREY
        ),
        padding=10,
        border_radius=8,
        bgcolor=ft.colors.BLUE_50
    )
    
    # Campos de entrada
    ecuacion_input = ft.TextField(
        label="Ecuación diferencial (y' = ...)",
        read_only=True,
        expand=True,
        border_radius=12,
        text_size=18,
        cursor_color=ft.colors.BLUE,
        filled=True
    )
    
    inputs_container = ft.Container(
        content=ft.Row([
            ft.TextField(label="t0", width=150, border_radius=12, ref=ft.Ref[ft.TextField]()),
            ft.TextField(label="y0", width=150, border_radius=12, ref=ft.Ref[ft.TextField]()),
            ft.TextField(label="tf", width=150, border_radius=12, ref=ft.Ref[ft.TextField]())
        ], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
        padding=ft.padding.only(top=10, bottom=10)
    )
    
    # Referencias a los campos para acceder después
    t0_input = inputs_container.content.controls[0]
    y0_input = inputs_container.content.controls[1]
    tf_input = inputs_container.content.controls[2]
    
    # Resultado y gráfica
    resultado_text = ft.Text(
        value="", 
        size=16, 
        selectable=True, 
        color=ft.colors.GREEN_700
    )
    
    grafica_imagen = ft.Image(
        visible=False,
        width=500,
        height=300,
        fit=ft.ImageFit.CONTAIN,
        border_radius=10
    )
    
    # Callbacks para los botones
    def agregar_simbolo(simbolo):
        def handler(e):
            ecuacion_input.value = (ecuacion_input.value or "") + simbolo
            page.update()
        return handler
    
    def limpiar_ecuacion(e):
        ecuacion_input.value = ""
        resultado_text.value = ""
        t0_input.value = ""
        y0_input.value = ""
        tf_input.value = ""
        grafica_imagen.visible = False
        nonlocal current_solution
        current_solution = None
        boton_grafica.disabled = True
        page.update()
    
    def crear_grafica_externa():
        """Crea una gráfica y la guarda en un archivo HTML para visualización externa"""
        try:
            t0 = solution_params["t0"]
            tf = solution_params["tf"]
            ecuacion = solution_params["equation"]
            
            if current_solution is None:
                return None
                
            # Crear el directorio temporal si no existe
            temp_dir = os.path.join(tempfile.gettempdir(), "calcediff")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Nombre de archivo único con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(temp_dir, f"grafica_{timestamp}.html")
            
            # Generar gráfica y guardarla como HTML
            t_vals = np.linspace(t0, tf, 500)
            y_vals = current_solution.sol(t_vals)[0]
            
            plt.figure(figsize=(10, 6))
            plt.plot(t_vals, y_vals, label="y(t)", color="royalblue", linewidth=2)
            plt.title(f"Solución de y' = {ecuacion}")
            plt.xlabel("t")
            plt.ylabel("y")
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.tight_layout()
            
            # Guardar como HTML con código embebido
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Gráfica de Ecuación Diferencial</title>
                <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .container {{ max-width: 800px; margin: 0 auto; }}
                    h2 {{ color: #2c3e50; }}
                    .equation {{ font-style: italic; margin-bottom: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Solución de la Ecuación Diferencial</h2>
                    <div class="equation">y' = {ecuacion}</div>
                    <canvas id="solutionChart" width="800" height="400"></canvas>
                </div>
                
                <script>
                    const ctx = document.getElementById('solutionChart').getContext('2d');
                    const chart = new Chart(ctx, {{
                        type: 'line',
                        data: {{
                            labels: {str([round(t, 3) for t in t_vals.tolist()])},
                            datasets: [{{
                                label: 'y(t)',
                                data: {str(y_vals.tolist())},
                                borderColor: 'rgba(65, 105, 225, 1)',
                                backgroundColor: 'rgba(65, 105, 225, 0.1)',
                                borderWidth: 2,
                                tension: 0.3,
                                pointRadius: 0
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            plugins: {{
                                title: {{
                                    display: true,
                                    text: 'Solución de la Ecuación Diferencial'
                                }},
                                tooltip: {{
                                    mode: 'index',
                                    intersect: false,
                                }}
                            }},
                            scales: {{
                                x: {{
                                    title: {{
                                        display: true,
                                        text: 't'
                                    }}
                                }},
                                y: {{
                                    title: {{
                                        display: true,
                                        text: 'y(t)'
                                    }}
                                }}
                            }}
                        }}
                    }});
                </script>
            </body>
            </html>
            """
            
            with open(file_path, "w") as f:
                f.write(html_content)
            
            plt.close()
            return file_path
            
        except Exception as e:
            print(f"Error al crear gráfica: {str(e)}")
            return None
    
    def mostrar_grafica_externa(e):
        if current_solution is None:
            show_error("Primero debes resolver la ecuación")
            return
        
        # Desactivar botón mientras se procesa
        boton_grafica.disabled = True
        estado_grafica.value = "Generando gráfica..."
        page.update()
        
        # Crear y abrir la gráfica en un hilo separado
        def worker():
            try:
                file_path = crear_grafica_externa()
                if file_path:
                    # Abrir en el navegador predeterminado
                    webbrowser.open(f"file://{file_path}")
                    page.invoke_async(lambda: setattr(estado_grafica, "value", "Gráfica abierta en navegador"))
                else:
                    page.invoke_async(lambda: setattr(estado_grafica, "value", "Error al generar gráfica"))
            except Exception as e:
                page.invoke_async(lambda: setattr(estado_grafica, "value", f"Error: {str(e)}"))
            finally:
                # Habilitar botón de nuevo
                page.invoke_async(lambda: setattr(boton_grafica, "disabled", False))
                page.update_async()
        
        # Iniciar hilo
        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()
    
    def resolver_ecuacion(e):
        try:
            # Validar que todos los campos tengan valores
            if not ecuacion_input.value or not t0_input.value or not y0_input.value or not tf_input.value:
                show_error("Todos los campos son obligatorios")
                return
            
            # Preparar la ecuación para evaluación
            expr_str = ecuacion_input.value.replace("^", "**")
            
            # Validar la expresión antes de evaluar
            try:
                # Las variables t e y serán sustituidas cuando se llame la función
                expr_lambda = eval(
                    f"lambda t, y: {expr_str}", 
                    {
                        "sin": np.sin, 
                        "cos": np.cos, 
                        "exp": np.exp, 
                        "log": np.log
                    }
                )
            except SyntaxError:
                show_error("La ecuación tiene errores de sintaxis")
                return
            except NameError as e:
                show_error(f"Variable no definida: {str(e)}")
                return
            
            # Convertir valores a números
            try:
                t0 = float(t0_input.value)
                y0 = float(y0_input.value)
                tf = float(tf_input.value)
            except ValueError:
                show_error("Los valores deben ser números")
                return
            
            # Validar el rango
            if tf <= t0:
                show_error("El tiempo final (tf) debe ser mayor que el tiempo inicial (t0)")
                return
            
            # Resolver la ecuación diferencial
            sol = solve_ivp(
                expr_lambda, 
                (t0, tf), 
                [y0], 
                dense_output=True,
                method='RK45',  # Método explícito de Runge-Kutta 4(5)
                rtol=1e-5  # Tolerancia relativa
            )
            
            if not sol.success:
                show_error("No se pudo resolver la ecuación diferencial")
                return
            
            # Guardar la solución para uso posterior
            nonlocal current_solution
            current_solution = sol
            
            # Guardar parámetros de la solución
            solution_params["t0"] = t0
            solution_params["tf"] = tf
            solution_params["equation"] = ecuacion_input.value
                
            y_final = sol.y[0][-1]
            show_success(f"✅ y({tf}) ≈ {y_final:.6f}")
            
            # Habilitar el botón de gráfica
            boton_grafica.disabled = False
            estado_grafica.value = "Haz clic en 'Ver gráfica' para visualizar"
            
            # Generar y mostrar la gráfica integrada
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmpfile:
                temp_path = tmpfile.name
                
                t_vals = np.linspace(t0, tf, 500)
                y_vals = sol.sol(t_vals)[0]
                
                plt.figure(figsize=(8, 5))
                plt.plot(t_vals, y_vals, label="y(t)", color="royalblue", linewidth=2)
                plt.title(f"Solución de y' = {ecuacion_input.value}")
                plt.xlabel("t")
                plt.ylabel("y")
                plt.grid(True, alpha=0.3)
                plt.legend()
                plt.tight_layout()
                plt.savefig(temp_path, dpi=100)
                plt.close()
                
                grafica_imagen.src = temp_path
                grafica_imagen.visible = True
                page.update()
                
        except Exception as err:
            show_error(str(err))
    
    # Botones de la calculadora
    botones = [
        ["+", "-", "*", "/", "^"],
        ["t", "y", "(", ")", "."],
        ["0", "1", "2", "3", "4"],
        ["5", "6", "7", "8", "9"],
        ["sin(t)", "cos(t)", "exp(t)", "log(t)"]
    ]
    
    botones_container = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.ElevatedButton(
                    text=b,
                    on_click=agregar_simbolo(b),
                    style=create_button_style(
                        color=ft.colors.BLUE_100 if b not in ["sin(t)", "cos(t)", "exp(t)", "log(t)"] 
                        else ft.colors.INDIGO_100
                    ),
                    width=100 if b in ["sin(t)", "cos(t)", "exp(t)", "log(t)"] else 60
                ) for b in fila
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=8)
            for fila in botones
        ]),
        padding=10
    )
    
    # Estado de la gráfica
    estado_grafica = ft.Text(
        value="", 
        size=14,
        italic=True,
        color=ft.colors.BLUE_GREY
    )
    
    # Botones principales
    boton_resolver = ft.ElevatedButton(
        "✅ Resolver",
        on_click=resolver_ecuacion,
        style=create_button_style(ft.colors.GREEN_500),
        icon=ft.icons.CALCULATE
    )
    
    boton_grafica = ft.ElevatedButton(
        "📈 Ver gráfica",
        on_click=mostrar_grafica_externa,
        style=create_button_style(ft.colors.BLUE_400),
        icon=ft.icons.SHOW_CHART,
        disabled=True
    )
    
    boton_limpiar = ft.OutlinedButton(
        "🧹 Limpiar",
        on_click=limpiar_ecuacion,
        style=create_button_style(None),
        icon=ft.icons.CLEAR
    )
    
    # Agregar todos los componentes a la página
    page.add(
        header,
        ft.Divider(thickness=2),
        instructions,
        ft.Container(height=10),  # Espaciador
        ecuacion_input,
        botones_container,
        ft.Divider(),
        inputs_container,
        ft.Row(
            [boton_resolver, boton_grafica, boton_limpiar], 
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20
        ),
        estado_grafica,
        ft.Divider(),
        resultado_text,
        grafica_imagen
    )

if __name__ == "__main__":
    ft.app(target=main)