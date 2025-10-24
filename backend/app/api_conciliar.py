from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
import io
import traceback

router = APIRouter()

def limpiar_monto(valor):
    if pd.isna(valor): return None
    try:
        val = str(valor).replace("B/.", "").replace("B/ ", "").replace("$", "").replace(",", ".")
        val = ''.join(c for c in val if c.isdigit() or c == '.' or c == '-')
        return round(float(val), 2)
    except: return None

def limpiar_fecha(valor):
    try:
        return pd.to_datetime(valor, dayfirst=True).date()
    except:
        return None

@router.post("/conciliar_auto")
async def conciliar_auto(
    cierre: UploadFile = File(...),
    yappy: UploadFile = File(...),
    banco: UploadFile = File(...)
):
    try:
        # --- Leer Cierre POS ---
        cierre_bytes = await cierre.read()
        df_cierre = pd.read_excel(io.BytesIO(cierre_bytes), engine="openpyxl")
        df_cierre.columns = [str(c).strip().lower() for c in df_cierre.columns]
        if "monto" not in df_cierre.columns or "fecha" not in df_cierre.columns:
            raise HTTPException(status_code=400, detail="Archivo de cierre no válido.")
        df_cierre["monto"] = df_cierre["monto"].apply(limpiar_monto)
        df_cierre["fecha"] = df_cierre["fecha"].apply(limpiar_fecha)

        # --- Leer Yappy ---
        yappy_bytes = await yappy.read()
        df_yappy = pd.read_excel(io.BytesIO(yappy_bytes), header=11, engine="openpyxl")
        df_yappy.columns = [str(c).strip().lower() for c in df_yappy.columns]
        col_fecha = next(c for c in df_yappy.columns if "fecha" in c)
        col_total = next(c for c in df_yappy.columns if "total" in c or "monto" in c)
        col_cliente = next(c for c in df_yappy.columns if "cliente" in c)
        df_yappy = df_yappy[[col_fecha, col_cliente, col_total]]
        df_yappy.columns = ["fecha", "cliente", "monto"]
        df_yappy["monto"] = df_yappy["monto"].apply(limpiar_monto)
        df_yappy["fecha"] = df_yappy["fecha"].apply(limpiar_fecha)

        # --- Leer Banco ---
        banco_bytes = await banco.read()
        df_banco = pd.read_excel(io.BytesIO(banco_bytes), header=6, engine="openpyxl")
        df_banco.columns = [str(c).strip().lower() for c in df_banco.columns]
        col_fecha = next(c for c in df_banco.columns if "fecha" in c)
        col_desc = next(c for c in df_banco.columns if "desc" in c)
        col_credito = next(c for c in df_banco.columns if "crédit" in c or "credit" in c)
        df_banco = df_banco[[col_fecha, col_desc, col_credito]]
        df_banco.columns = ["fecha", "descripcion", "monto"]
        df_banco["monto"] = df_banco["monto"].apply(limpiar_monto)
        df_banco["fecha"] = df_banco["fecha"].apply(limpiar_fecha)

        # --- Unificar y comparar ---
        df_cierre["origen"] = "CIERRE"
        df_yappy["origen"] = "YAPPY"
        df_banco["origen"] = "BANCO"

        df_all = pd.concat([df_cierre, df_yappy, df_banco], ignore_index=True)

        # Detectar coincidencias exactas
        conc = []
        for _, row in df_yappy.iterrows():
            match_cierre = df_cierre[
                (df_cierre["monto"] == row["monto"]) & (df_cierre["fecha"] == row["fecha"])
            ]
            match_banco = df_banco[
                (df_banco["monto"] == row["monto"]) & (df_banco["fecha"] == row["fecha"])
            ]

            if not match_cierre.empty and not match_banco.empty:
                estado = "COINCIDE"
            elif not match_cierre.empty or not match_banco.empty:
                estado = "MONTO_OK_NOMBRE_DIF"
            else:
                estado = "SIN_MATCH"

            conc.append({
                "fecha": str(row["fecha"]),
                "cliente": row["cliente"],
                "monto": row["monto"],
                "estado": estado
            })

        df_conc = pd.DataFrame(conc)

        resumen = df_conc["estado"].value_counts().to_dict()

        return {
            "ok": True,
            "total_registros": len(df_conc),
            "resumen": resumen,
            "preview": df_conc.head(50).to_dict(orient="records")
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error conciliando: {e}")
