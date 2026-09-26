# Analizador Léxico

Proyecto de Compiladores. Analizador léxico hecho con Flex, con una interfaz gráfica en Python para probarlo.

## Lenguaje usado

- Flex (C) para el analizador léxico en si
- Python con Tkinter para la interfaz grafica

## Que se necesita para correrlo

- flex y gcc instalados
- Python 3 con tkinter

Para compilar el analizador:

```
cd lexer
flex analizador.l
gcc lex.yy.c -o analizador
```

Para correr la interfaz:

```
cd gui
python3 analizador_gui.py
```

Se escribe o carga el codigo, se le da click a "Analizar" y salen los tokens en la tabla.

## Logica del analizador

En `analizador.l` se define una expresion regular por cada tipo de token: palabras reservadas, identificadores, numeros, operadores, simbolos, cadenas y comentarios. Flex toma esas reglas y genera un programa en C que las convierte en un automata: el programa va leyendo el codigo caracter por caracter y en cada punto trata de reconocer el token mas largo posible con las reglas que definimos. Cuando ya no puede seguir alargando el token, lo reporta y sigue con el siguiente.

Si un caracter no hace match con ninguna regla, se reporta como error lexico.

Los lexemas que se reconocen, mas o menos asi:

| Tipo | Como se forma |
|---|---|
| Palabra reservada | int, float, char, double, void, if, else, while, for, do, return, break, continue, struct |
| Identificador | empieza con letra (a/z, A/Z) o guion bajo, y despues puede seguir con letras, numeros o guion bajo |
| Numero entero | uno o mas digitos (0-9) |
| Numero decimal | digitos, un punto, y mas digitos |
| Cadena | texto entre comillas dobles |
| Operador relacional | ==, !=, <=, >=, <, > |
| Operador logico | &&, \|\|, ! |
| Operador aritmetico | +, -, *, /, % |
| Operador de asignacion | = |
| Simbolo | ( ) { } [ ] ; , |
| Comentario de linea | empieza con // y termina al final de esa linea |
| Comentario de bloque | todo lo que este entre /* y */, puede abarcar varias lineas |
| Error lexico | cualquier caracter que no encaje en ninguna de las anteriores |

La interfaz grafica no hace ningun analisis por su cuenta, solo le manda el codigo al programa compilado y muestra lo que este devuelve en una tabla.
