import sqlite3
import pandas as pd
import numpy as np

def conectar_db():
    return sqlite3.connect('inventario.db')

def cargar_datos():
    conn = conectar_db()
    df = pd.read_sql_query("SELECT * FROM productos", conn)
    conn.close()
    return df

def preparar_datos(df):
    df['promedio_costo'] = df[['costo_unitario_mes1', 'costo_unitario_mes2', 'costo_unitario_mes3']].mean(axis=1)
    df['valor_total'] = df['promedio_costo'] * df['stock_actual']
    df.sort_values(by='valor_total', ascending=False, inplace=True)
    df['porcentaje_acumulado'] = df['valor_total'].cumsum() / df['valor_total'].sum()
    df['clasificacion_abc'] = pd.cut(df['porcentaje_acumulado'],
                                     bins=[0, 0.8, 0.95, 1.0],
                                     labels=['A', 'B', 'C'])

    # Punto de Reorden
    lead_time = 2
    df['punto_reorden'] = df['consumo_mensual'] * lead_time

    # Cantidad Economica de Pedido
    S = 100  # Costo por pedido
    df['demanda_anual'] = df['consumo_mensual'] * 12
    df['costo_mantenimiento'] = 0.2 * df['promedio_costo']
    df['eoq'] = np.sqrt((2 * df['demanda_anual'] * S) / df['costo_mantenimiento'])
    return df

def mostrar_clasificacion_abc(df):
    print("\n Clasificación ABC de productos:\n")
    print(df[['nombre', 'valor_total', 'clasificacion_abc']].head(20))

def mostrar_punto_reorden(df):
    print("\n Punto de Reorden (ROP):\n")
    print(df[['nombre', 'consumo_mensual', 'punto_reorden']].head(20))

def mostrar_eoq(df):
    print("\n Cantidad Económica de Pedido (EOQ):\n")
    print(df[['nombre', 'demanda_anual', 'eoq']].head(20))

def mostrar_reporte_completo(df):
    print("\n Reporte completo:\n")
    print(df[['nombre', 'clasificacion_abc', 'punto_reorden', 'eoq']].head(20))

def menu():
    while True:
        print("\n--- MENÚ DE INVENTARIO ---")
        print("1. Clasificación ABC")
        print("2. Punto de Reorden")
        print("3. Cantidad Económica de Pedido (EOQ)")
        print("4. Ver Reporte Completo")
        print("5. Salir")
        opcion = input("Selecciona una opción: ")

        df = preparar_datos(cargar_datos())

        if opcion == '1':
            mostrar_clasificacion_abc(df)
        elif opcion == '2':
            mostrar_punto_reorden(df)
        elif opcion == '3':
            mostrar_eoq(df)
        elif opcion == '4':
            mostrar_reporte_completo(df)
        elif opcion == '5':
            print("¡Hasta luego!")
            break
        else:
            print("Opción no válida. Intenta de nuevo.")

menu()
