/*
 * analizador.l
 * -------------------------------------------------------------------------
 * Analizador Lexico para un mini-lenguaje similar a C, construido con Flex.
 *
 * Autor: Edwin (edwinsitoflete28@gmail.com)
 *
 * Funcionamiento:
 *   El programa lee codigo fuente por la ENTRADA ESTANDAR (stdin) y para
 *   cada token que reconoce imprime UNA linea en formato CSV por la
 *   SALIDA ESTANDAR (stdout):
 *
 *       TIPO_TOKEN,LEXEMA,NUMERO_DE_LINEA
 *
 *   Esta salida estructurada es la que despues consume la interfaz grafica
 *   (hecha en Python/Tkinter) para mostrar la tabla de tokens. Asi el
 *   nucleo del analisis lexico (el automata que genera Flex) queda
 *   totalmente separado de la presentacion visual.
 *
 * Compilacion manual (ver tambien README.md):
 *   flex analizador.l
 *   gcc lex.yy.c -o analizador -lfl
 * -------------------------------------------------------------------------
 */

%{
#include <stdio.h>
#include <string.h>

/*
 * Emite una linea CSV: TIPO,"LEXEMA",LINEA
 * El lexema va siempre entre comillas (formato CSV estandar) para que
 * pueda contener comas, comillas o saltos de linea sin romper las
 * columnas. Las comillas internas se duplican ("") y los saltos de
 * linea reales se representan como \n para mantener un token por linea.
 */
static void emitir(const char *tipo, const char *lexema, int linea) {
    printf("%s,\"", tipo);
    for (const char *p = lexema; *p; p++) {
        if (*p == '"') printf("\"\"");     /* comilla interna -> "" */
        else if (*p == '\n') printf("\\n"); /* salto de linea real -> \n literal */
        else putchar(*p);
    }
    printf("\",%d\n", linea);
}
%}

%option noyywrap
%option yylineno

DIGITO       [0-9]
LETRA        [a-zA-Z_]
ENTERO       {DIGITO}+
DECIMAL      {DIGITO}+"."{DIGITO}+
ID           {LETRA}({LETRA}|{DIGITO})*

%%

"//"[^\n]*                              { emitir("COMENTARIO_LINEA", yytext, yylineno); }

"/*"([^*]|\*+[^*/])*\*+"/"              { emitir("COMENTARIO_BLOQUE", yytext, yylineno); }

"int"|"float"|"char"|"double"|"void"|"if"|"else"|"while"|"for"|"do"|"return"|"break"|"continue"|"struct" {
                                           emitir("PALABRA_RESERVADA", yytext, yylineno); }

{ID}                                     { emitir("IDENTIFICADOR", yytext, yylineno); }

{DECIMAL}                                { emitir("NUMERO_DECIMAL", yytext, yylineno); }
{ENTERO}                                 { emitir("NUMERO_ENTERO", yytext, yylineno); }

\"([^\"\\\n]|\\.)*\"                     { emitir("CADENA", yytext, yylineno); }

"=="|"!="|"<="|">="|"<"|">"              { emitir("OP_RELACIONAL", yytext, yylineno); }
"&&"|"\|\|"|"!"                          { emitir("OP_LOGICO", yytext, yylineno); }
"+"|"-"|"*"|"/"|"%"                      { emitir("OP_ARITMETICO", yytext, yylineno); }
"="                                      { emitir("OP_ASIGNACION", yytext, yylineno); }

"("|")"|"{"|"}"|"["|"]"|";"|","          { emitir("SIMBOLO", yytext, yylineno); }

[ \t\r]+                                 { /* espacios en blanco: se ignoran */ }
\n                                       { /* saltos de linea: se ignoran (yylineno ya cuenta) */ }

.                                        { emitir("ERROR_LEXICO", yytext, yylineno); }

%%

/*
 * main() propio: asi el programa NO depende de libfl (-lfl), lo cual
 * hace que compile igual en Linux (gcc) y en Windows con un MinGW
 * portatil (w64devkit) + win_flex, sin tener que buscar esa libreria.
 */
int main(void) {
    yylex();
    return 0;
}
