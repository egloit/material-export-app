"""
Material Export Application - Streamlit Version
Main Application Entry Point
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import re
from pathlib import Path

from config import Config, LogConfig
from services.database_service import DatabaseService
from services.calculation_service import CalculationService
from services.export_service import ExportService
from services.excel_calculation_service import ExcelCalculationService
from utils.parsers import parse_material_input, parse_dimensions, split_test_parts
from utils.logger import CalculationLogger

try:
    APP_VERSION = (Path(__file__).parent / "VERSION").read_text().strip()
except FileNotFoundError:
    APP_VERSION = "unknown"

# Page Configuration
st.set_page_config(
    page_title="Packaging calculation System",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
div[data-testid="stButton"] button[kind="tertiary"] { color: #e00; padding: 0; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None
if 'logger' not in st.session_state:
    st.session_state.logger = None


def render_sidebar():
    """Render sidebar with settings"""
    with st.sidebar:
        st.title("⚙️ Settings")

        st.subheader("🔍 Logging")
        LogConfig.ENABLED = st.checkbox("Enable Logging", value=LogConfig.ENABLED)

        if LogConfig.ENABLED:
            with st.expander("Details", expanded=False):
                LogConfig.LOG_DB_QUERIES = st.checkbox("DB Queries", value=LogConfig.LOG_DB_QUERIES)
                LogConfig.LOG_CALCULATIONS = st.checkbox("Calculations", value=LogConfig.LOG_CALCULATIONS)
                LogConfig.LOG_RULES = st.checkbox("Supplier Rules", value=LogConfig.LOG_RULES)
                LogConfig.LOG_DATA_SOURCE = st.checkbox("Data Sources", value=LogConfig.LOG_DATA_SOURCE)

            col1, col2 = st.columns(2)
            with col1:
                LogConfig.LOG_TO_UI = st.checkbox("Show in UI", value=LogConfig.LOG_TO_UI)
            with col2:
                LogConfig.LOG_TO_FILE = st.checkbox("Write to File", value=LogConfig.LOG_TO_FILE)

        st.divider()
        Config.DEBUG_SHEET = st.checkbox("🐛 Debug Output", value=Config.DEBUG_SHEET)

        st.divider()
        Config.EXCEL_ENABLED = st.checkbox(
            "📊 Excel-based Calculation",
            value=Config.EXCEL_ENABLED,
            help="Use formulas library to compute costs directly from supplier Excel files"
        )

        st.divider()
        st.subheader("📁 Supplier Excel Files")
        upload_folder = Path(Config.EXCEL_FOLDER)
        upload_folder.mkdir(parents=True, exist_ok=True)

        uploaded = st.file_uploader(
            "Upload new supplier (.xlsx)",
            type=["xlsx"],
            accept_multiple_files=True,
            help="Uploaded files are stored persistently and override base files with the same name.",
        )
        if uploaded:
            for f in uploaded:
                dest = upload_folder / f.name
                dest.write_bytes(f.getvalue())
            st.success(f"{len(uploaded)} file(s) saved.")

        excel_svc = st.session_state.get("excel_service")
        base_folder = Path(Config.EXCEL_BASE_FOLDER)
        blocklist = excel_svc._get_blocklist() if excel_svc else set()

        active: dict[str, str] = {}   # name -> "base" | "uploaded"
        blocked: list[str] = []       # blocked base suppliers (not overridden by upload)

        uploaded_stems = {
            f.stem.lower()
            for f in upload_folder.glob("*.xlsx")
            if not f.name.startswith("~$")
        } if upload_folder.is_dir() else set()

        if base_folder.is_dir():
            for f in sorted(base_folder.glob("*.xlsx")):
                if f.name.startswith("~$"):
                    continue
                if f.stem.lower() in blocklist and f.stem.lower() not in uploaded_stems:
                    blocked.append(f.stem)
                else:
                    active[f.stem] = "base"
        if upload_folder.is_dir():
            for f in sorted(upload_folder.glob("*.xlsx")):
                if not f.name.startswith("~$"):
                    active[f.stem] = "uploaded"

        if active:
            with st.expander(f"Active suppliers ({len(active)})", expanded=False):
                for name, source in sorted(active.items()):
                    tag = "⬆️" if source == "uploaded" else "📦"
                    col_btn, col_name = st.columns([1, 5], vertical_alignment="center")
                    if col_btn.button("✕", key=f"del_{name}", help=f"Delete {name}.xlsx", type="tertiary"):
                        if source == "uploaded":
                            (upload_folder / f"{name}.xlsx").unlink(missing_ok=True)
                        if source == "base" and excel_svc:
                            excel_svc.block_base_supplier(name)
                        st.rerun()
                    col_name.caption(f"{tag} {name}")
        else:
            st.caption("No supplier files found.")

        if blocked:
            with st.expander(f"Hidden base suppliers ({len(blocked)})", expanded=False):
                for name in sorted(blocked):
                    col_btn, col_name = st.columns([1, 5], vertical_alignment="center")
                    if col_btn.button("↩", key=f"restore_{name}", help=f"Restore {name}", type="tertiary"):
                        if excel_svc:
                            excel_svc.unblock_base_supplier(name)
                        st.rerun()
                    col_name.caption(f"🚫 {name}")

        st.divider()
        st.caption(f"v{APP_VERSION}")


def main():
    """Main application"""
    render_sidebar()

    # Initialize services
    config = Config()
    logger = CalculationLogger(LogConfig())
    db_service = DatabaseService(config, logger)
    export_service = ExportService(logger)

    # Initialize Excel service if enabled
    excel_service = None
    if config.EXCEL_ENABLED:
        excel_service = ExcelCalculationService(config, logger)
    st.session_state.excel_service = excel_service

    calc_service = CalculationService(config, logger, excel_service=excel_service)

    # Show results or input form
    if st.session_state.results:
        show_results(st.session_state.results, st.session_state.logger, export_service)

        st.divider()
        if st.button("⬅️ Enter New Materials", width='stretch'):
            st.session_state.results = None
            st.session_state.logger = None
            st.rerun()
    else:
        tab_sap, tab_test = st.tabs(["SAP Material", "New Part (Test)"])
        with tab_sap:
            show_input_form(db_service, calc_service, logger)
        with tab_test:
            show_test_part_form(excel_service, logger)


def show_input_form(db_service, calc_service, logger):
    """Show material input form"""
    st.title("📦 Packaging calculation System")

    st.markdown("""
    Enter material numbers, one per line.

    **Optional dimensions:**
    - `KM0290 100x380x535` (with x separator)
    - `KM0290;100;380;535` (with semicolon separator)

    **New part test (without SAP material):**
    - `KM_TEST 150 X 250 X 300_3PLY_I` (Box Type_TEST L X B X H_Ply_Design Type)
    """)

    material_input = st.text_area(
        "Material Numbers",
        height=200,
        placeholder="KM0290 100x380x535\nKM1234\nKM5678;120;95;80\nKRTB_TEST 150 X 250 X 300_3PLY_U"
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔍 Submit & Show Table", type="primary", width='stretch'):
            process_materials(material_input, db_service, calc_service, logger)


@st.cache_data(show_spinner=False)
def load_row_groups(_excel_service, files_signature):
    """Sl.No. groups of all suppliers; re-read whenever a supplier file changes."""
    return _excel_service.list_all_row_groups()


DESIGN_LABELS = {'U': 'U (Universal)', 'I': 'I (Interlock)', 'Inlay': 'Inlay'}


def show_test_part_form(excel_service, logger):
    """Calculate test prices for a new part without SAP material"""
    st.title("🧪 New Part (Test)")

    if not (Config.EXCEL_ENABLED and excel_service):
        st.warning("Enable 'Excel-based Calculation' in the sidebar to calculate test prices.")
        return

    groups = load_row_groups(excel_service, excel_service.files_signature())
    if not groups:
        st.warning("No supplier Excel files found.")
        return

    col1, col2, col3 = st.columns(3)
    boxes = sorted({g['box'] for g in groups})
    box = col1.selectbox("Box Type", boxes, index=boxes.index('KM') if 'KM' in boxes else 0, key="tp_box")
    groups = [g for g in groups if g['box'] == box]
    ply = col2.selectbox("Ply Type", sorted({g['ply'] for g in groups}), key="tp_ply")
    groups = [g for g in groups if g['ply'] == ply]
    design = col3.selectbox(
        "Design Type", sorted({g['design'] for g in groups}),
        format_func=lambda d: DESIGN_LABELS.get(d, d or '-'), key="tp_design"
    )
    groups = [g for g in groups if g['design'] == design]

    is_inlay = design == 'Inlay'
    col1, col2, col3, col4 = st.columns(4)
    L = col1.number_input("L (mm)", min_value=1, value=150, step=1, key="tp_L")
    B = col2.number_input("B (mm)", min_value=1, value=250, step=1, key="tp_B")
    H = col3.number_input("H (mm)", min_value=1, value=300, step=1, key="tp_H", disabled=is_inlay)
    if is_inlay:
        H = 0

    auto_size = '> 300 mm' if L > 300 else '< 300 mm'
    size_choice = col4.selectbox(
        "Size Type", ["auto", "< 300 mm", "> 300 mm"],
        format_func=lambda s: f"{auto_size} (auto from L)" if s == "auto" else s, key="tp_size"
    )
    size = auto_size if size_choice == "auto" else size_choice
    # Groups without Size Type (e.g. Interlock, Inlay) apply to any size
    groups = [g for g in groups if not g['size'] or g['size'] == size]

    if not groups:
        st.warning(f"No calculation row for {box} / {ply} / {design} / {size}.")
        return

    group = st.radio(
        "Matching calculation",
        groups,
        format_func=lambda g: f"Sl.No. {g['sl_no']} – {g['desc']}  ({', '.join(sorted(g['rows']))})",
        key="tp_group",
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if not st.button("💰 Calculate Test Price", type="primary", width='stretch'):
            return

    key = f"TEST Sl.No. {group['sl_no']}"
    with st.spinner("Calculating..."):
        excel_results = excel_service.compute_all_suppliers_for_group(group['rows'], L, B, H)

    st.session_state.results = {
        'enhanced_rows': [{
            'SAP Material Nr': key,
            'SAP Description': group['desc'],
            'L': L,
            'B': B,
            'H': H,
            'PLY TYPE': ply,
            'BOX TYPE': box,
            'SIZE TYPE': size,
            'DESIGN TYPE': design,
        }],
        'excel_results_by_key': {0: excel_results},
    }
    st.session_state.logger = logger
    st.rerun()


def process_materials(material_input, db_service, calc_service, logger):
    """Process material input and query database"""
    if not material_input.strip():
        st.error("Please enter at least one material number.")
        return

    # Parse input
    with st.spinner("Parsing..."):
        test_lines, sap_input = split_test_parts(material_input)
        mat_array, dim_overrides = parse_material_input(sap_input, logger) if sap_input.strip() else ([], {})

    if not mat_array and not test_lines:
        st.error("No valid material numbers found.")
        return

    st.success(f"Found {len(mat_array)} material(s)"
               + (f" and {len(test_lines)} test part(s)" if test_lines else ""))

    # Query SAP
    sap_rows = []
    if mat_array:
        with st.spinner("Querying database..."):
            try:
                sap_rows = db_service.get_sap_master_data(mat_array)
            except Exception as e:
                st.error(f"Database error: {str(e)}")
                return

        found = {row['SAP Material Nr'] for row in sap_rows}
        not_found = [m for m in mat_array if m not in found]
        if not sap_rows and not test_lines:
            st.warning("No materials found in SAP.")
            return
    else:
        not_found = []

    # New-part test lines have no SAP record: the line itself serves as
    # material number and description (box type, dimensions, ply, design)
    sap_rows += [{'SAP Material Nr': line, 'SAP Description': line} for line in test_lines]

    # Process each material
    with st.spinner("Processing..."):
        enhanced_rows = []
        excel_results_by_key = {}

        for sap_row in sap_rows:
            matnr = sap_row['SAP Material Nr']
            desc = sap_row.get('SAP Description', '')
            parsed = parse_dimensions(desc)
            ov = dim_overrides.get(matnr)

            # Extract types
            box_match = re.match(r'^[A-Z]+', matnr)
            box_type = box_match.group(0) if box_match else ''

            ply_type = parsed['TYPE']
            if not ply_type:
                ply_match = re.search(r'(\d+)\s*Ply', desc, re.IGNORECASE)
                if ply_match:
                    ply_type = f"{ply_match.group(1)} Ply"

            # Size type
            if ov and ov.get('L') and ov['L'].isdigit():
                size_type = '> 300 mm' if float(ov['L']) > 300 else '< 300 mm'
            elif '< 300 mm' in desc.lower():
                size_type = '< 300 mm'
            elif '> 300 mm' in desc.lower():
                size_type = '> 300 mm'
            else:
                L_for_size = parsed['L']
                size_type = '> 300 mm' if (L_for_size and float(L_for_size) > 300) else '< 300 mm'

            # Design type
            design_type = ''
            desc_trim = desc.rstrip()
            if desc_trim and desc_trim[-1] != ')':
                design_type = desc_trim[-1].upper()

            # Dimensions (resolved) – fall back to '1' if a value is missing
            L_val = (ov['L'] if ov else parsed['L']) or '1'
            B_val = (ov['M'] if ov else parsed['B']) or '1'
            H_val = (ov['N'] if ov else parsed['H']) or '1'

            enhanced_rows.append({
                'SAP Material Nr': matnr,
                'SAP Description': desc,
                'L': L_val,
                'B': B_val,
                'H': H_val,
                'PLY TYPE': ply_type,
                'BOX TYPE': box_type,
                'SIZE TYPE': size_type,
                'DESIGN TYPE': design_type
            })

            # Excel-based calculation for all suppliers
            if Config.EXCEL_ENABLED and calc_service.excel_service:
                L_num = float(L_val) if L_val else 0.0
                B_num = float(B_val) if B_val else 0.0
                H_num = float(H_val) if H_val else 0.0

                if L_num > 0 and B_num > 0 and H_num > 0:
                    excel_results = calc_service.compute_all_suppliers_from_excel(
                        ply_type, box_type, size_type, design_type, L_num, B_num, H_num
                    )
                    # Keyed by row: SAP can return several descriptions per material
                    excel_results_by_key[len(enhanced_rows) - 1] = excel_results

    # Store in session
    st.session_state.results = {
        'enhanced_rows': enhanced_rows,
        'excel_results_by_key': excel_results_by_key,
        'not_found': not_found,
    }
    st.session_state.logger = logger
    st.rerun()


def show_results(results, logger, export_service):
    """Show results table"""
    st.title("✅ Found Materials")

    enhanced_rows = results['enhanced_rows']
    excel_results_by_key = results.get('excel_results_by_key', {})

    if results.get('not_found'):
        st.warning("Not found in SAP: " + ", ".join(results['not_found']))

    # Main table
    df_main = pd.DataFrame(enhanced_rows)
    st.dataframe(df_main, width='stretch', hide_index=True)

    # Excel-based supplier costs (all suppliers side by side)
    if excel_results_by_key:
        st.divider()
        st.subheader("📊 Excel-based Supplier Costs")

        for idx, row_data in enumerate(enhanced_rows):
            matnr = row_data['SAP Material Nr']
            excel_results = excel_results_by_key.get(idx, {})

            if not excel_results:
                continue

            with st.expander(
                f"📊 {matnr} - {row_data['SAP Description']} "
                f"(L={row_data['L']}, B={row_data['B']}, H={row_data['H']})",
                expanded=True
            ):
                show_excel_supplier_costs(excel_results)

    # CSV Download
    st.divider()
    csv_data = export_service.export_to_csv(enhanced_rows)
    st.download_button(
        "💾 Download CSV",
        data=csv_data,
        file_name=f"material_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        width='stretch'
    )

    # Logs
    if LogConfig.ENABLED and LogConfig.LOG_TO_UI and logger:
        st.divider()
        with st.expander("📋 Calculation Log", expanded=False):
            st.text_area("Logs", value=logger.get_logs(), height=400, disabled=True)
            st.download_button(
                "💾 Download Log",
                data=logger.get_logs(),
                file_name=f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )


def show_excel_supplier_costs(excel_results: dict):
    """Display all supplier costs from Excel calculation in a comparison table."""
    # Build summary table: one row per supplier
    summary_data = []
    for supplier, result in sorted(excel_results.items()):
        if result is None:
            summary_data.append({
                'Supplier': supplier,
                'AJ Row 1': '-',
                'AJ Row 2': '-',
                'AJ Row 3': '-',
                'Final Cost (AK)': 'N/A',
            })
        else:
            aj = result['AJ']
            summary_data.append({
                'Supplier': supplier,
                'AJ Row 1': f"{aj[0]:.4f}" if len(aj) > 0 else '-',
                'AJ Row 2': f"{aj[1]:.4f}" if len(aj) > 1 else '-',
                'AJ Row 3': f"{aj[2]:.4f}" if len(aj) > 2 else '-',
                'Final Cost (AK)': f"{result['AK']:.2f}",
            })

    if summary_data:
        df = pd.DataFrame(summary_data)

        # Find cheapest supplier (lowest numeric AK)
        cheapest_idx = None
        cheapest_cost = float('inf')
        for idx, row in df.iterrows():
            try:
                cost = float(row['Final Cost (AK)'])
                if cost < cheapest_cost:
                    cheapest_cost = cost
                    cheapest_idx = idx
            except (ValueError, TypeError):
                continue

        def highlight_cheapest(row):
            if row.name == cheapest_idx:
                return ['background-color: #d4edda'] * len(row)
            return [''] * len(row)

        styled_df = df.style.apply(highlight_cheapest, axis=1)
        st.dataframe(styled_df, width='stretch', hide_index=True)

    # Detailed view per supplier (expandable)
    for supplier, result in sorted(excel_results.items()):
        if result is None:
            continue

        with st.expander(f"🏢 {supplier} - Details (Row {result.get('start_row', '?')})", expanded=False):
            detail_data = []
            for rd in result.get('rows', []):
                detail_data.append({
                    'Row': str(rd['row']),
                    'T (Width")': f"{rd['T']:.4f}" if rd['T'] is not None else '-',
                    'U (Height")': f"{rd['U']:.4f}" if rd['U'] is not None else '-',
                    'V (Weight)': f"{rd['V']:.6f}" if rd['V'] is not None else '-',
                    'W (Mat.Cost)': f"{rd['W']:.4f}" if rd['W'] is not None else '-',
                    'Z (Total Mat.)': f"{rd['Z']:.4f}" if rd['Z'] is not None else '-',
                    'AF (Process)': f"{rd['AF']:.4f}" if rd['AF'] is not None else '-',
                    'AJ (Price)': f"{rd['AJ']:.6f}",
                })

            detail_data.append({
                'Row': None,
                'T (Width")': '',
                'U (Height")': '',
                'V (Weight)': '',
                'W (Mat.Cost)': '',
                'Z (Total Mat.)': '',
                'AF (Process)': 'TOTAL',
                'AJ (Price)': f"{result['AK']:.2f}",
            })

            df_detail = pd.DataFrame(detail_data)
            st.dataframe(df_detail, width='stretch', hide_index=True)


if __name__ == "__main__":
    main()
