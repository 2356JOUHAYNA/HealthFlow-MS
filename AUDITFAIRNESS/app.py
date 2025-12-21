import os
import json
from datetime import datetime, timedelta

import pandas as pd
import psycopg2

from dash import Dash, html, dcc
from dash.dependencies import Input, Output
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, DataQualityPreset

# =========================
# CONFIG
# =========================
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "healthflow")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

PORT = int(os.getenv("PORT", "8050"))
REPORTS_DIR = os.getenv("REPORTS_DIR", "/app/reports")

# =========================
# DB
# =========================
def get_conn():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )

def load_dataset(start, end):
    sql = """
    SELECT
        rs.patient_pseudo_id,
        rs.risk_level,
        rs.confidence,
        rs.created_at,

        -- 🔽 CAST SAFE depuis JSONB
        (pf.features_json ->> 'age')::float                AS age,
        pf.features_json ->> 'gender'                      AS gender,
        (pf.features_json ->> 'conditions_total')::float   AS conditions_total,
        (pf.features_json ->> 'medications_total')::float  AS medications_total

    FROM risk_scores rs
    JOIN patient_features pf
      ON rs.patient_pseudo_id = pf.patient_pseudo_id
    WHERE rs.created_at BETWEEN %s AND %s
    """

    with get_conn() as conn:
        df = pd.read_sql(sql, conn, params=(start, end))

    if df.empty:
        return df

    # =========================
    # GROUPES FAIRNESS
    # =========================
    df["age_group"] = pd.cut(
        df["age"],
        bins=[0, 18, 35, 50, 65, 120],
        labels=["0-18", "19-35", "36-50", "51-65", "66+"]
    )

    df["comorbidity_group"] = pd.cut(
        df["conditions_total"],
        bins=[-1, 0, 2, 5, 1000],
        labels=["0", "1-2", "3-5", "6+"]
    )

    return df


def save_report_metadata(ref_df, cur_df, path):
    sql = """
    INSERT INTO fairness_reports
    (ref_start, ref_end, cur_start, cur_end, report_path, summary)
    VALUES (%s, %s, %s, %s, %s, %s)
    """

    summary = {
        "reference_rows": int(len(ref_df)),
        "current_rows": int(len(cur_df)),
        "generated_at": datetime.utcnow().isoformat()
    }

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (
                ref_df["created_at"].min(),
                ref_df["created_at"].max(),
                cur_df["created_at"].min(),
                cur_df["created_at"].max(),
                path,
                json.dumps(summary)
            ))
        conn.commit()

# =========================
# EVIDENTLY
# =========================
def generate_report(ref_df, cur_df):
    # =========================
    # Nettoyage colonnes vides
    # =========================
    common_columns = [
        col for col in ref_df.columns
        if col in cur_df.columns
        and not ref_df[col].isna().all()
        and not cur_df[col].isna().all()
    ]

    # On garde toujours created_at pour Evidently
    if "created_at" not in common_columns:
        common_columns.append("created_at")

    ref_df_clean = ref_df[common_columns].copy()
    cur_df_clean = cur_df[common_columns].copy()

    report = Report(metrics=[
        DataQualityPreset(),
        DataDriftPreset()
    ])

    report.run(
        reference_data=ref_df_clean,
        current_data=cur_df_clean
    )

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = f"{REPORTS_DIR}/fairness_report_{ts}.html"
    report.save_html(path)

    save_report_metadata(ref_df_clean, cur_df_clean, path)

    return path


# =========================
# DASH APP
# =========================
app = Dash(__name__)
server = app.server

app.layout = html.Div(style={"padding": "20px", "fontFamily": "Arial"}, children=[
    html.H2("🧪 AuditFairness — Fairness & Drift Monitoring"),

    html.Div(style={"marginBottom": "10px"}, children=[
        html.Label("Référence (jours)"),
        dcc.Input(id="ref_days", type="number", value=14, min=1),
        html.Label("Courant (jours)", style={"marginLeft": "20px"}),
        dcc.Input(id="cur_days", type="number", value=7, min=1),
        html.Button("Générer", id="btn", n_clicks=0, style={"marginLeft": "20px"})
    ]),

    html.Hr(),
    html.Div(id="status", style={"marginBottom": "10px"}),
    html.Iframe(id="frame", style={"width": "100%", "height": "900px", "border": "1px solid #ddd"})
])

@app.callback(
    Output("status", "children"),
    Output("frame", "src"),
    Input("btn", "n_clicks"),
    Input("ref_days", "value"),
    Input("cur_days", "value")
)
def run_audit(n_clicks, ref_days, cur_days):
    if n_clicks == 0:
        return "Clique sur « Générer » pour lancer un audit.", ""

    now = datetime.utcnow()

    ref_end = now - timedelta(days=cur_days)
    ref_start = ref_end - timedelta(days=ref_days)

    cur_start = now - timedelta(days=cur_days)
    cur_end = now

    ref_df = load_dataset(ref_start, ref_end)
    cur_df = load_dataset(cur_start, cur_end)

    # 🔥 LOGIQUE COLD START (CRUCIALE)
    if ref_df.empty and not cur_df.empty:
        ref_df = cur_df.copy()

    if cur_df.empty and not ref_df.empty:
        cur_df = ref_df.copy()

    if ref_df.empty and cur_df.empty:
        return "❌ Aucune donnée disponible pour l’audit.", ""

    path = generate_report(ref_df, cur_df)
    filename = os.path.basename(path)

    return f"✅ Rapport généré : {filename}", f"/reports/{filename}"

# =========================
# SERVE REPORTS
# =========================
@server.route("/reports/<path:filename>")
def serve_report(filename):
    from flask import send_from_directory
    return send_from_directory(REPORTS_DIR, filename)

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=PORT)
