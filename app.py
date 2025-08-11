import streamlit as st
import pandas as pd
from io import BytesIO
from pathlib import Path
from datetime import date as dtdate
import os

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = str(BASE_DIR / "issuance_data.csv")
STOCK_FILE = str(BASE_DIR / "stock_data.csv")


def load_csv_data(file, columns):
    if os.path.exists(file):
        try:
            return pd.read_csv(file).to_dict('records')
        except Exception:
            return []
    else:
        return []


def save_csv_data(file, data, columns):
    try:
        df = pd.DataFrame(data)
        df = df[columns] if not df.empty else df
        Path(file).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(file, index=False)
    except Exception:
        pass


st.set_page_config(page_title="Explosives Data Entry", layout="wide", page_icon="💣")

# Ensure session state initialization happens before any access (including sidebar)
if 'data' not in st.session_state:
    st.session_state['data'] = load_csv_data(
        DATA_FILE,
        [
            "Date",
            "Mine",
            "Issued By",
            "Received By",
            "Remarks",
            "Wabox Cartridges",
            "Detonators",
            "Safety Fuse (m)",
        ],
    )
if 'stock' not in st.session_state:
    st.session_state['stock'] = load_csv_data(
        STOCK_FILE, ["Serial No", "Receiving Date", "Explosive Type", "Quantity"]
    )

# Sidebar with logo and info
with st.sidebar:
    st.image("https://img.icons8.com/ios-filled/100/000000/mining.png", width=80)
    st.title("Explosives Logbook")
    st.caption("Developed for Mining Engineers")
    st.markdown("---")
    st.subheader(":gear: User Settings")
    # Add new mine
    if 'mines' not in st.session_state:
        st.session_state['mines'] = ["Mine1", "Mine2", "Mine3"]
    with st.form("add_mine_form", clear_on_submit=True):
        new_mine = st.text_input("Add New Mine Name", max_chars=30, placeholder="e.g. Mine4")
        add_mine_btn = st.form_submit_button("Add Mine")
        if add_mine_btn and new_mine:
            if new_mine not in st.session_state['mines']:
                st.session_state['mines'].append(new_mine)
                st.success(f"Added mine: {new_mine}")
            else:
                st.warning("Mine already exists.")
    # Rename mines
    if st.session_state['mines']:
        st.markdown("**Rename Existing Mines**")
        for i, mine in enumerate(st.session_state['mines']):
            new_name = st.text_input(f"Rename {mine}", value=mine, key=f"rename_{i}", help="Change the name of this mine")
            if new_name != mine and new_name:
                # Update all previous entries in data
                for entry in st.session_state['data']:
                    if entry['Mine'] == mine:
                        entry['Mine'] = new_name
                st.session_state['mines'][i] = new_name
                st.success(f"Renamed {mine} to {new_name}")


# Main content with tabs for navigation
st.title("💣 Explosives Data Entry for Mines")
explosive_types = ["Wabox Cartridges", "Detonators", "Safety Fuse (m)"]

tab1, tab2, tab3 = st.tabs(["🚚 Issuance", "📦 Stock", "📊 Reports"])

# Helper: Calculate stock balance
def get_stock_balance():
    # Calculate total received
    if 'stock' in st.session_state and st.session_state['stock']:
        stock_df = pd.DataFrame(st.session_state['stock'])
        received = stock_df.groupby('Explosive Type')['Quantity'].sum()
    else:
        received = pd.Series(0, index=explosive_types)
    # Calculate total issued
    if 'data' in st.session_state and st.session_state['data']:
        issued_df = pd.DataFrame(st.session_state['data'])
        issued = issued_df[[t for t in explosive_types]].sum()
    else:
        issued = pd.Series(0, index=explosive_types)
    # Calculate balance
    balance = received.subtract(issued, fill_value=0)
    return balance


# Helper: Generate reports
def get_reports():
    reports = {}
    # Summary report
    if 'data' in st.session_state and st.session_state['data']:
        df = pd.DataFrame(st.session_state['data'])
        df['Date'] = pd.to_datetime(df['Date'])
        df['Month'] = df['Date'].dt.to_period('M')
        reports['Summary'] = df.groupby('Mine')[["Wabox Cartridges", "Detonators", "Safety Fuse (m)"]].sum().reset_index()
        # Monthly report
        reports['Monthly'] = df.groupby(['Month', 'Mine'])[["Wabox Cartridges", "Detonators", "Safety Fuse (m)"]].sum().reset_index()
        # Mine-wise report
        reports['Mine-wise'] = df.groupby(['Mine', 'Month'])[["Wabox Cartridges", "Detonators", "Safety Fuse (m)"]].sum().reset_index()
        # Full data
        reports['All Data'] = df
    else:
        reports['Summary'] = pd.DataFrame()
        reports['Monthly'] = pd.DataFrame()
        reports['Mine-wise'] = pd.DataFrame()
        reports['All Data'] = pd.DataFrame()
    return reports


with tab1:
    st.header("🚚 Issuance Entry")
    with st.form("entry_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            date = st.date_input("Date of Issue", value=dtdate.today(), help="Date when explosives are issued")
        mine = st.selectbox("Select Mine", st.session_state["mines"], help="Choose the mine to issue explosives")
        with c2:
            issued_by = st.text_input("Issued By", max_chars=30, placeholder="e.g. Engineer Name", help="Person issuing the explosives")
            received_by = st.text_input("Received By", max_chars=30, placeholder="e.g. Blaster Name", help="Person receiving the explosives")
        with c3:
            remarks = st.text_input("Remarks", max_chars=50, placeholder="Any remarks", help="Additional notes or remarks")

        st.markdown("---")
        st.markdown("#### Explosive Quantities")
        col1, col2, col3 = st.columns(3)
        with col1:
            wabox = st.number_input("Wabox Cartridges", min_value=0, step=1, help="Number of Wabox cartridges issued")
        with col2:
            detonators = st.number_input("Detonators", min_value=0, step=1, help="Number of detonators issued")
        with col3:
            fuse = st.number_input("Safety Fuse (meters)", min_value=0, step=1, help="Meters of safety fuse issued")

        submitted = st.form_submit_button("Add Entry", use_container_width=True)
        if submitted:
            st.session_state['data'].append({
                "Date": date,
                "Mine": mine,
                "Issued By": issued_by,
                "Received By": received_by,
                "Remarks": remarks,
                "Wabox Cartridges": wabox,
                "Detonators": detonators,
                "Safety Fuse (m)": fuse
            })
            save_csv_data(DATA_FILE, st.session_state['data'], ["Date","Mine","Issued By","Received By","Remarks","Wabox Cartridges","Detonators","Safety Fuse (m)"])
            st.success(f"✅ Entry added for {mine} on {date}.")

    # Issuance summary cards
    if st.session_state['data']:
        df = pd.DataFrame(st.session_state['data'])
        df['Date'] = pd.to_datetime(df['Date'])
        df['Month'] = df['Date'].dt.to_period('M')
        st.markdown("---")
        st.subheader(":bar_chart: Issuance Dashboard")
        k1, k2, k3 = st.columns(3)
        with k1:
            st.metric("Total Wabox Cartridges", int(df['Wabox Cartridges'].sum()))
        with k2:
            st.metric("Total Detonators", int(df['Detonators'].sum()))
        with k3:
            st.metric("Total Safety Fuse (m)", int(df['Safety Fuse (m)'].sum()))
        st.dataframe(df, use_container_width=True)

    # Show current stock balance and low stock warning
    st.markdown("---")
    st.subheader(":warning: Stock Balance (Real-Time)")
    balance = get_stock_balance()
    b1, b2, b3 = st.columns(3)
    min_threshold = 10  # Example threshold for low stock
    with b1:
        st.metric("Available Wabox Cartridges", int(balance.get("Wabox Cartridges", 0)))
        if balance.get("Wabox Cartridges", 0) <= min_threshold:
            st.warning("Low Wabox Cartridges stock!")
    with b2:
        st.metric("Available Detonators", int(balance.get("Detonators", 0)))
        if balance.get("Detonators", 0) <= min_threshold:
            st.warning("Low Detonators stock!")
    with b3:
        st.metric("Available Safety Fuse (m)", int(balance.get("Safety Fuse (m)", 0)))
        if balance.get("Safety Fuse (m)", 0) <= min_threshold:
            st.warning("Low Safety Fuse stock!")

with tab2:
    st.header("📦 Stock Receipt")
    if 'stock' not in st.session_state:
        st.session_state['stock'] = []
    with st.form("add_stock_form", clear_on_submit=True):
        stock_serial = st.text_input("Serial No.", max_chars=30, placeholder="e.g. S12345", help="Stock serial number")
        stock_date = st.date_input("Receiving Date", value=dtdate.today(), key="stock_date", help="Date stock was received")
        stock_type = st.selectbox("Explosive Type", ["Wabox Cartridges", "Detonators", "Safety Fuse (m)"], help="Type of explosive received")
        stock_qty = st.number_input("Quantity Received", min_value=0, step=1, help="Quantity of explosive received")
        add_stock_btn = st.form_submit_button("Add Stock")
        if add_stock_btn and stock_qty > 0 and stock_serial:
            st.session_state['stock'].append({
                "Serial No": stock_serial,
                "Receiving Date": stock_date,
                "Explosive Type": stock_type,
                "Quantity": stock_qty
            })
            save_csv_data(STOCK_FILE, st.session_state['stock'], ["Serial No","Receiving Date","Explosive Type","Quantity"])
            st.success(f"✅ Added stock: {stock_type} - {stock_qty}")
        elif add_stock_btn:
            st.warning("Please enter serial no and quantity.")

    # Stock summary cards
    if st.session_state['stock']:
        stock_df = pd.DataFrame(st.session_state['stock'])
        st.markdown("---")
        st.subheader(":bar_chart: Stock Dashboard")
        s1, s2, s3 = st.columns(3)
        with s1:
            st.metric("Total Wabox Cartridges", int(stock_df[stock_df['Explosive Type']=="Wabox Cartridges"]['Quantity'].sum()))
        with s2:
            st.metric("Total Detonators", int(stock_df[stock_df['Explosive Type']=="Detonators"]['Quantity'].sum()))
        with s3:
            st.metric("Total Safety Fuse (m)", int(stock_df[stock_df['Explosive Type']=="Safety Fuse (m)"]['Quantity'].sum()))
        st.dataframe(stock_df, use_container_width=True)

# Footer

with tab3:
    st.header("📊 Reports & Downloads")
    reports = get_reports()
    report_type = st.selectbox("Select Report Type", ["Summary", "Monthly", "Mine-wise", "All Data"], help="Choose the type of report to view and download")
    df_report = reports[report_type]
    if not df_report.empty:
        st.dataframe(df_report, use_container_width=True)
        # Download as Excel
        def to_excel(df):
            # Ensure Period columns (e.g., 'Month') are cast to string for Excel compatibility
            df_to_write = df.copy()
            if 'Month' in df_to_write.columns:
                df_to_write['Month'] = df_to_write['Month'].astype(str)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_to_write.to_excel(writer, index=False, sheet_name=report_type)
            return output.getvalue()
        excel_data = to_excel(df_report)
        st.download_button(
            label=f"Download {report_type} Report as Excel",
            data=excel_data,
            file_name=f"{report_type.lower().replace(' ', '_')}_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("No data available for this report.")

st.markdown("---")
st.markdown("<center>Made with ❤️ for Mining Engineers | For support: mining-support@example.com</center>", unsafe_allow_html=True)

# Display stock table and current stock summary
if 'stock' in st.session_state and st.session_state['stock']:
    st.subheader(":inbox_tray: Stock Receipts")
    stock_df = pd.DataFrame(st.session_state['stock'])
    st.dataframe(stock_df, use_container_width=True)
    # Current stock summary
    stock_summary = stock_df.groupby('Explosive Type')['Quantity'].sum().reset_index()
    st.markdown("#### :bar_chart: Current Stock in Magazine")
    st.dataframe(stock_summary, use_container_width=True)

# Display data table and dashboard
if st.session_state['data']:
    df = pd.DataFrame(st.session_state['data'])
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.to_period('M')

    # Filters
    with st.expander(":mag: Filter Data", expanded=False):
        f1, f2 = st.columns(2)
        with f1:
            mine_filter = st.multiselect("Filter by Mine", st.session_state["mines"], default=st.session_state["mines"])
        with f2:
            date_range = st.date_input("Date Range", [df['Date'].min(), df['Date'].max()])
        mask = (
            df['Mine'].isin(mine_filter) &
            (df['Date'] >= pd.to_datetime(date_range[0])) &
            (df['Date'] <= pd.to_datetime(date_range[1]))
        )
        df_filtered = df[mask]

    # Dashboard summary
    st.markdown("### :bar_chart: Dashboard Summary")
    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric("Total Wabox Cartridges", int(df_filtered['Wabox Cartridges'].sum()))
    with k2:
        st.metric("Total Detonators", int(df_filtered['Detonators'].sum()))
    with k3:
        st.metric("Total Safety Fuse (m)", int(df_filtered['Safety Fuse (m)'].sum()))

    # Chart
    chart_data = df_filtered.groupby('Mine')[["Wabox Cartridges", 'Detonators', 'Safety Fuse (m)']].sum().reset_index()
    st.bar_chart(chart_data.set_index('Mine'))

    st.subheader(":clipboard: Issued Explosives Data")
    st.dataframe(df_filtered, use_container_width=True)

    # Monthly summary
    monthly_summary = df_filtered.groupby(['Month', 'Mine'], as_index=False)[['Wabox Cartridges', 'Detonators', 'Safety Fuse (m)']].sum()
    st.subheader(":calendar: Monthly Summary")
    st.dataframe(monthly_summary, use_container_width=True)

    # Download as Excel with two sheets
    def to_excel_with_summary(df, monthly_summary):
        # Ensure Period columns (e.g., 'Month') are cast to string for Excel compatibility
        df_to_write = df.copy()
        if 'Month' in df_to_write.columns:
            df_to_write['Month'] = df_to_write['Month'].astype(str)
        monthly_to_write = monthly_summary.copy()
        if 'Month' in monthly_to_write.columns:
            monthly_to_write['Month'] = monthly_to_write['Month'].astype(str)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_to_write.to_excel(writer, index=False, sheet_name='Issued Explosives')
            monthly_to_write.to_excel(writer, index=False, sheet_name='Monthly Summary')
        return output.getvalue()

    excel_data = to_excel_with_summary(df_filtered, monthly_summary)
    st.download_button(
        label="Download Excel Sheet",
        data=excel_data,
        file_name="explosives_issued.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info(":information_source: No data entered yet.")


