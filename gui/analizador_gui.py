#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analizador_gui.py
------------------------------------------------------------------------
Interfaz grafica (Tkinter) para el Analizador Lexico construido con Flex.

Esta aplicacion NO implementa el analisis lexico por si misma: se limita a
enviar el codigo fuente escrito por el usuario al ejecutable generado por
Flex (lexer/analizador) y a mostrar, en una tabla, los tokens que ese
ejecutable reconoce. Toda la logica del automata vive en lexer/analizador.l

Autor: Edwin (edwinsitoflete28@gmail.com)

Ejecucion:
    python3 analizador_gui.py
(en algunos sistemas puede ser necesario "python3.12 analizador_gui.py",
 ver README.md)
------------------------------------------------------------------------
"""

import csv
import io
import os
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Ruta al ejecutable generado por Flex+gcc (lexer/analizador), relativa a
# este archivo, para que funcione sin importar desde donde se ejecute.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_LEXER_DIR = os.path.join(BASE_DIR, "..", "lexer")


def resolver_ejecutable():
    """Devuelve la ruta al binario correcto para esta plataforma.

    En Windows SIEMPRE se prefiere "analizador.exe": si además existe un
    binario "analizador" sin extension (por ejemplo, compilado en Linux y
    copiado por error junto al proyecto), NO debe usarse ahi, porque no es
    un ejecutable Win32 valido y el sistema fallaria con WinError 193.
    """
    candidatos = (
        ["analizador.exe", "analizador"] if os.name == "nt" else ["analizador"]
    )
    for nombre in candidatos:
        ruta = os.path.join(_LEXER_DIR, nombre)
        if os.path.isfile(ruta):
            return ruta
    # Ninguno existe: devolvemos la ruta preferida de todas formas para
    # que los mensajes de error de mas abajo apunten a un nombre sensato.
    return os.path.join(_LEXER_DIR, candidatos[0])


EJECUTABLE = resolver_ejecutable()

CODIGO_EJEMPLO = """// Escribe aqui tu codigo o carga un archivo
int suma(int a, int b) {
    float resultado = a + b * 2;
    if (resultado >= 10 && a != 0) {
        resultado = resultado - 1;
    }
    return resultado;
}
"""

COLOR_ERROR = "#f8d7da"      # fondo para filas de ERROR_LEXICO
COLOR_COMENTARIO = "#e2e3e5" # fondo para comentarios
COLOR_NORMAL_1 = "#ffffff"
COLOR_NORMAL_2 = "#f3f6fa"


class AnalizadorLexicoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Analizador Lexico - Flex")
        self.root.geometry("980x650")
        self.root.minsize(760, 480)

        self._verificar_ejecutable()
        self._construir_interfaz()

    # ------------------------------------------------------------------
    # Construccion de la interfaz
    # ------------------------------------------------------------------
    def _construir_interfaz(self):
        contenedor = ttk.Frame(self.root, padding=10)
        contenedor.pack(fill="both", expand=True)

        # --- Barra superior (titulo + botones) ---------------------------
        barra = ttk.Frame(contenedor)
        barra.pack(fill="x", pady=(0, 8))

        titulo = ttk.Label(
            barra, text="Analizador Lexico (Flex)", font=("Segoe UI", 14, "bold")
        )
        titulo.pack(side="left")

        ttk.Button(barra, text="Cargar archivo...", command=self.cargar_archivo).pack(
            side="right", padx=(6, 0)
        )
        ttk.Button(barra, text="Limpiar", command=self.limpiar).pack(
            side="right", padx=(6, 0)
        )
        self.btn_analizar = ttk.Button(
            barra, text="Analizar", command=self.analizar
        )
        self.btn_analizar.pack(side="right", padx=(6, 0))

        # --- Panel dividido: codigo fuente | tabla de tokens --------------
        panel = ttk.PanedWindow(contenedor, orient="horizontal")
        panel.pack(fill="both", expand=True)

        # Panel izquierdo: entrada de codigo fuente
        marco_izq = ttk.Frame(panel)
        ttk.Label(marco_izq, text="Codigo fuente a analizar:").pack(
            anchor="w", pady=(0, 4)
        )
        self.texto_codigo = tk.Text(
            marco_izq, wrap="none", font=("Consolas", 11), undo=True
        )
        self.texto_codigo.insert("1.0", CODIGO_EJEMPLO)
        scroll_y = ttk.Scrollbar(
            marco_izq, orient="vertical", command=self.texto_codigo.yview
        )
        self.texto_codigo.configure(yscrollcommand=scroll_y.set)
        self.texto_codigo.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")
        panel.add(marco_izq, weight=1)

        # Panel derecho: tabla de tokens resultante
        marco_der = ttk.Frame(panel)
        ttk.Label(marco_der, text="Tokens reconocidos:").pack(anchor="w", pady=(0, 4))

        columnas = ("tipo", "lexema", "linea")
        self.tabla = ttk.Treeview(
            marco_der, columns=columnas, show="headings", height=15
        )
        self.tabla.heading("tipo", text="Token")
        self.tabla.heading("lexema", text="Lexema")
        self.tabla.heading("linea", text="Linea")
        self.tabla.column("tipo", width=150, anchor="w")
        self.tabla.column("lexema", width=220, anchor="w")
        self.tabla.column("linea", width=60, anchor="center")

        scroll_tabla = ttk.Scrollbar(
            marco_der, orient="vertical", command=self.tabla.yview
        )
        self.tabla.configure(yscrollcommand=scroll_tabla.set)
        self.tabla.pack(side="left", fill="both", expand=True)
        scroll_tabla.pack(side="right", fill="y")
        panel.add(marco_der, weight=1)

        self.tabla.tag_configure("error", background=COLOR_ERROR)
        self.tabla.tag_configure("comentario", background=COLOR_COMENTARIO)
        self.tabla.tag_configure("par", background=COLOR_NORMAL_2)
        self.tabla.tag_configure("impar", background=COLOR_NORMAL_1)

        # --- Barra inferior: resumen / estado ------------------------------
        self.estado = tk.StringVar(
            value="Listo. Escribe o carga codigo y presiona 'Analizar'."
        )
        barra_estado = ttk.Label(
            contenedor, textvariable=self.estado, anchor="w", relief="sunken", padding=4
        )
        barra_estado.pack(fill="x", pady=(8, 0))

    # ------------------------------------------------------------------
    # Verificaciones
    # ------------------------------------------------------------------
    def _verificar_ejecutable(self):
        if not os.path.isfile(resolver_ejecutable()):
            messagebox.showwarning(
                "Ejecutable no encontrado",
                "No se encontro el ejecutable del analizador en:\n"
                f"{os.path.abspath(ruta)}\n\n"
                "Compilalo primero desde la carpeta 'lexer' con:\n"
                "  flex analizador.l\n"
                "  gcc lex.yy.c -o analizador -lfl\n\n"
                "(Ver README.md para mas detalles)",
            )

    # ------------------------------------------------------------------
    # Acciones de la interfaz
    # ------------------------------------------------------------------
    def cargar_archivo(self):
        ruta = filedialog.askopenfilename(
            title="Selecciona un archivo de codigo fuente",
            filetypes=[("Archivos de texto/codigo", "*.txt *.c *.h *.txt"), ("Todos", "*.*")],
        )
        if not ruta:
            return
        try:
            with open(ruta, "r", encoding="utf-8", errors="replace") as f:
                contenido = f.read()
        except OSError as e:
            messagebox.showerror("Error al leer archivo", str(e))
            return
        self.texto_codigo.delete("1.0", "end")
        self.texto_codigo.insert("1.0", contenido)
        self.estado.set(f"Archivo cargado: {ruta}")

    def limpiar(self):
        self.texto_codigo.delete("1.0", "end")
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        self.estado.set("Listo.")

    def analizar(self):
        codigo = self.texto_codigo.get("1.0", "end")

        ejecutable = resolver_ejecutable()

        if not os.path.isfile(ejecutable):
            messagebox.showerror(
                "Ejecutable no encontrado",
                "No se pudo ejecutar el analizador. Compila el proyecto "
                "de Flex primero (ver README.md).",
            )
            return

        try:
            resultado = subprocess.run(
                [ejecutable],
                input=codigo,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except Exception as e:  # noqa: BLE001 - mostramos cualquier fallo al usuario
            messagebox.showerror("Error al ejecutar el analizador", str(e))
            return

        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        if resultado.returncode != 0:
            messagebox.showerror(
                "El analizador termino con error",
                resultado.stderr or "Error desconocido al ejecutar el analizador.",
            )
            return

        lineas = resultado.stdout.splitlines()
        lector = csv.reader(io.StringIO(resultado.stdout))

        total = 0
        errores = 0
        conteo_por_tipo = {}

        for i, fila_csv in enumerate(lector):
            if len(fila_csv) < 3:
                continue
            tipo, lexema, numero_linea = fila_csv[0], fila_csv[1], fila_csv[2]
            total += 1
            conteo_por_tipo[tipo] = conteo_por_tipo.get(tipo, 0) + 1

            if tipo == "ERROR_LEXICO":
                etiqueta = "error"
                errores += 1
            elif tipo.startswith("COMENTARIO"):
                etiqueta = "comentario"
            else:
                etiqueta = "par" if i % 2 == 0 else "impar"

            self.tabla.insert(
                "", "end", values=(tipo, lexema, numero_linea), tags=(etiqueta,)
            )

        if errores > 0:
            self.estado.set(
                f"Analisis completo: {total} tokens, {errores} error(es) lexico(s) "
                f"resaltado(s) en rojo."
            )
        else:
            self.estado.set(f"Analisis completo: {total} tokens reconocidos, sin errores.")


def main():
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except tk.TclError:
        pass
    AnalizadorLexicoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
