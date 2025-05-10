# Branch Franco
import sqlite3, math
import pandas as pd
import numpy as np

def conectar_db():
    with sqlite3.connect('inventario.db', detect_types = sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES) as conexion:
        cursor = conexion.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS PRODUCTOS(
                           id INTEGER,
                           nombre TEXT,
                           stock_actual INTEGER,
                           consumo_mensual INTEGER,
                           tiempo_entrega REAL,
                           costo_unitario_mes1 REAL,
                           costo_unitario_mes2 REAL,
                           costo_unitario_mes3 REAL,
                           CONSTRAINT PK_PRODUCTO PRIMARY KEY (id)
                       );
                       ''')
    
    return sqlite3.connect('inventario.db')

def cargar_datos():
    conn = conectar_db()
    df = pd.read_sql_query("SELECT * FROM productos", conn)
    df.columns = ["Id", "Producto", "Stock Actual", "Consumo Mensual", "Tiempo de Entrega", "Costo Unitario Mes 1", "Costo Unitario Mes 2", "Costo Unitario Mes 3"]
    conn.close()
    return df

def preparar_datos(df):
    
    # DF para Clasificación ABC
    def clasificar_ABC(porcentaje):
        if porcentaje <= 0.8:
            return "A"
        
        elif porcentaje <= 0.95:
            return "B"
        
        else:
            return "C"
        
    df_abc = pd.DataFrame()
    
    df_abc["Producto"] = df["Producto"]
    df_abc["Costo Unitario Mes 1"] = df["Costo Unitario Mes 1"]
    df_abc["Costo Unitario Mes 2"] = df["Costo Unitario Mes 2"]
    df_abc["Costo Unitario Mes 3"] = df["Costo Unitario Mes 3"]
    df_abc["Promedio"] = df_abc[["Costo Unitario Mes 1", "Costo Unitario Mes 2", "Costo Unitario Mes 3"]].mean(axis = 1)
    
    df_abc = df_abc.sort_values(by = "Promedio", ascending = False).reset_index(drop = True)
    
    porcentaje_Acumulado = (df_abc["Promedio"] / df_abc["Promedio"].sum()).cumsum()
    
    df_abc["Clasificación ABC"] = porcentaje_Acumulado.apply(clasificar_ABC)
    
    # DF Punto de Reorden
    df_Punto_Reorden = pd.DataFrame()
    df_Punto_Reorden["Producto"] = df["Producto"]
    df_Punto_Reorden["Consumo Mensual"] = df["Consumo Mensual"]
    df_Punto_Reorden["Tiempo de Entrega"] = df["Tiempo de Entrega"]
    df_Punto_Reorden["Stock de Seguridad"] = df["Consumo Mensual"] * 0.2
    df_Punto_Reorden["Stock de Seguridad"] = df_Punto_Reorden["Stock de Seguridad"].round(0)
    df_Punto_Reorden["Punto de Reorden"] = (df_Punto_Reorden["Consumo Mensual"] * df_Punto_Reorden["Tiempo de Entrega"]) + df_Punto_Reorden["Stock de Seguridad"]
    df_Punto_Reorden["Punto de Reorden"] = df_Punto_Reorden["Punto de Reorden"].round(0)
    
    # DF Cantidad Económica de Pedido
    df_eoq = pd.DataFrame()
    df_eoq["Producto"] = df["Producto"]
    df_eoq["Demanda Anual"] = df["Consumo Mensual"] * 12
    df_eoq["Costo por Pedido"] = df[["Costo Unitario Mes 1", "Costo Unitario Mes 2", "Costo Unitario Mes 3"]].mean(axis = 1) * 0.15
    df_eoq["Costo Anual por Mantener"] = df[["Costo Unitario Mes 1", "Costo Unitario Mes 2", "Costo Unitario Mes 3"]].mean(axis = 1) * .05
    df_eoq["Cantidad Económica de Pedido"] = np.sqrt((2 * df_eoq["Demanda Anual"] * df_eoq["Costo por Pedido"]) / df_eoq["Costo Anual por Mantener"])
    df_eoq["Cantidad Económica de Pedido"] = df_eoq["Cantidad Económica de Pedido"].round(0)
    
    # DF Reporte Final
    df_final = pd.DataFrame()
    df_final["Producto"] = df["Producto"]
    df_final = df_final.merge(df_abc[["Producto", "Clasificación ABC"]], on = "Producto", how = "left")
    df_final["Punto de Reorden"] = df_Punto_Reorden["Punto de Reorden"]
    df_final["Cantidad Económica de Pedido"] = df_eoq["Cantidad Económica de Pedido"]

    return df, df_abc, df_Punto_Reorden, df_eoq, df_final

def menu():
    pd.set_option('display.max_rows', None)
    
    while True:
        print("\n--- MENÚ DE INVENTARIO ---")
        print("1. Clasificación ABC")
        print("2. Punto de Reorden")
        print("3. Cantidad Económica de Pedido (EOQ)")
        print("4. Ver Reporte Completo")
        print("5. Mostrar datos")
        print("6. Salir")
        opcion = input("Selecciona una opción: ")

        df, df_abc, df_Punto_Reorden, df_eoq, df_final = preparar_datos(cargar_datos())
        
        if opcion == "6":
            print("\n¡Hasta luego!")
            break
            
        elif df.empty:
            print("\nActualmente no se cuenta con ningún producto.")
        
        else:
            match opcion:
                # CASO 1. ABC
                case "1":
                    print("\nClasificación ABC de productos:\n")
                    print(df_abc)
                    
                # CASO 2. PUNTO DE REORDEN
                case "2":
                    print("\nPunto de Reorden (ROP):\n")
                    print(df_Punto_Reorden)
                    
                # CASO 3. EOQ
                case "3":
                    print("\nCantidad Económica de Pedido (EOQ):\n")
                    print(df_eoq)
                
                # CASO 4. REPORTE
                case "4":
                    print("\nReporte Completo:\n")
                    print(df_final)
                
                # CASO 5. DATOS
                case "5":
                    print("\nDatos Completos:\n")
                    df = df.iloc[:, 1:]
                    print(df)
                
                case _:
                    print("\nOpción no válida. Intente de nuevo.")

menu()