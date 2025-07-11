import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from PIL import Image #⭐️ IMPORT PIL

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="🚀 Advanced Business Pulse Monitor",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DATA LOADING & FEATURE ENGINEERING ---
@st.cache_data
def load_data():
    """Loads, cleans, and adds features like moving averages."""
    try:
        df = pd.read_csv("kpi_forecasts_with_alerts.csv")
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values(by="Date")
        for col in ['Sales_USD_Act', 'Sales_USD_For', 'Support_Tickets', 'Support_Tickets_For', 'Retention_Rate', 'Retention_Rate_For']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['Sales_7_Day_MA'] = df['Sales_USD_Act'].rolling(window=7, min_periods=1).mean()
        df['Support_7_Day_MA'] = df['Support_Tickets'].rolling(window=7, min_periods=1).mean()
        return df
    except FileNotFoundError:
        st.error("Error: The file 'kpi_forecasts_with_alerts.csv' was not found.")
        return None

# --- STYLING & HELPER FUNCTIONS ---
def style_alerts_table(df):
    """Highlights alerts in the dataframe."""
    def highlight_alerts(val):
        if not isinstance(val, str): return ''
        color = '#F88379' if 'Critical' in val else '#FFD580' if 'Warning' in val else ''
        return f'background-color: {color}'
    alert_cols = [col for col in df.columns if 'Alert' in col]
    return df.style.applymap(highlight_alerts, subset=alert_cols)

# --- MAIN APP LOGIC ---
df = load_data()
if df is None or df.empty:
    st.stop()
# ⭐️ ADDED LOGO
try:
    logo = Image.open("logo.png")
    st.sidebar.image(logo)
except FileNotFoundError:
    st.sidebar.warning("Logo file not found. Please add 'logo.png' to the directory.")
# ⭐️ END OF LOGO CODE

# --- SIDEBAR ---
st.sidebar.title("Controls & Filters")


def set_date_range(days):
    max_date = df['Date'].max().date()
    st.session_state.date_range = (max_date - timedelta(days=days), max_date)

st.sidebar.subheader("Preset Date Ranges")
col1, col2, col3 = st.sidebar.columns(3)
if col1.button("Last 7 Days"):
    set_date_range(7)
if col2.button("Last 30 Days"):
    set_date_range(30)
if col3.button("Last 90 Days"):
    set_date_range(90)

if 'date_range' not in st.session_state:
    st.session_state.date_range = (df['Date'].min().date(), df['Date'].max().date())

date_range = st.sidebar.date_input(
    "Or Select Custom Range:",
    value=st.session_state.date_range,
    min_value=df['Date'].min().date(),
    max_value=df['Date'].max().date(),
    key='date_range'
)

st.sidebar.subheader("🎯 Business Goals")
sales_goal = st.sidebar.number_input("Daily Sales Goal ($)", value=100000, step=1000)
support_goal = st.sidebar.number_input("Max Daily Support Tickets", value=600, step=10)
retention_goal = st.sidebar.number_input("Target Retention Rate (%)", value=95.0, step=0.5) / 100

# Filter dataframe
filtered_df = df[(df['Date'].dt.date >= date_range[0]) & (df['Date'].dt.date <= date_range[1])]
if filtered_df.empty:
    st.warning("No data available for the selected date range.")
    st.stop()

# Download Button
st.sidebar.markdown("---")
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.sidebar.download_button("📥 Download Filtered Data", csv, "filtered_data.csv", "text/csv")
st.sidebar.markdown("---")
st.sidebar.text_area("Forecasting Assumptions:", "Assumes no major marketing campaigns or service outages during the forecast period.", height=100)
st.sidebar.write("Built by Sameer Shaik")

# --- HEADER ---
with st.container():
    st.title("🚀 Advanced Business Pulse Monitor")
    st.markdown("This interactive dashboard provides AI-powered forecasts and deeper analytics for key business metrics.")
    st.markdown("---")

latest_data = filtered_df.iloc[-1]

# --- DYNAMIC ALERTS PANEL ---
with st.expander("🚨 Key Alerts & Insights", expanded=True):
    alert_found = False
    if latest_data['Sales_USD_Act'] < sales_goal:
        st.error(f"Sales Alert: Latest sales of ${latest_data['Sales_USD_Act']:,.0f} missed the goal of ${sales_goal:,.0f}.")
        alert_found = True
    if latest_data['Sales_USD_Act'] < latest_data['Sales_USD_For']:
        st.warning(f"Sales Warning: Latest sales fell short of the forecast of ${latest_data['Sales_USD_For']:,.0f}.")
        alert_found = True
    if latest_data['Support_Tickets'] > support_goal:
        st.error(f"Support Alert: Ticket volume of {latest_data['Support_Tickets']} exceeded the goal of {support_goal}.")
        alert_found = True
    if latest_data['Retention_Rate'] < retention_goal:
        st.error(f"Retention Alert: Rate of {latest_data['Retention_Rate']:.2%} is below the goal of {retention_goal:.2%}.")
        alert_found = True
    if not alert_found:
        st.success("✅ All Good! All key metrics are meeting their goals and forecasts.")

st.markdown("---")

# --- TABS FOR EACH KPI ---
tab1, tab2, tab3 = st.tabs(["📈 Sales Performance", "🎫 Support Tickets", "🎯 Customer Retention"])

with tab1:
    st.header("Sales Performance")
    sales_delta = latest_data['Sales_USD_Act'] - latest_data['Sales_USD_For']
    st.metric(label="Latest Daily Sales", value=f"${latest_data['Sales_USD_Act']:,.0f}", delta=f"${sales_delta:,.0f} vs. Forecast")
    sales_fig = px.line(
        filtered_df, x='Date',
        y=['Sales_USD_Act', 'Sales_USD_For', 'Sales_7_Day_MA'],
        labels={'value': 'Sales (USD)', 'variable': 'Metric Type'},
        title="Sales: Actual vs. Forecast vs. 7-Day Trend", markers=False
    )
    sales_fig.data[2].update(line_color='rgba(255,0,0,0.6)', line_dash='dash')
    sales_fig.add_hline(y=sales_goal, line_dash="dot", annotation_text="Sales Goal", line_color="red")
    st.plotly_chart(sales_fig, use_container_width=True)

with tab2:
    st.header("Support Ticket Volume")
    support_delta = latest_data['Support_Tickets'] - latest_data['Support_Tickets_For']
    st.metric(label="Latest Daily Tickets", value=f"{int(latest_data['Support_Tickets'])}", delta=f"{int(support_delta)} vs. Forecast", delta_color="inverse")
    support_fig = px.line(
        filtered_df, x='Date',
        y=['Support_Tickets', 'Support_Tickets_For', 'Support_7_Day_MA'],
        labels={'value': 'Number of Tickets', 'variable': 'Metric Type'},
        title="Support Tickets: Actual vs. Forecast vs. 7-Day Trend", markers=False
    )
    support_fig.data[2].update(line_color='rgba(255,0,0,0.6)', line_dash='dash')
    support_fig.add_hline(y=support_goal, line_dash="dot", annotation_text="Max Tickets Goal", line_color="red")
    st.plotly_chart(support_fig, use_container_width=True)
    st.markdown("---")
    st.subheader("Daily Ticket Volume Heatmap")
    try:
        from calplot import calplot
        fig_cal = calplot(filtered_df, x='Date', y='Support_Tickets', dark_theme=False, month_lines_width=3)
        st.plotly_chart(fig_cal, use_container_width=True)
    except ImportError:
        st.warning("Please install `plotly_calplot` to view the calendar heatmap: `pip install plotly_calplot`")
    except Exception as e:
        st.error(f"Could not generate calendar heatmap. Error: {e}")

with tab3:
    st.header("Customer Retention")
    retention_delta = latest_data['Retention_Rate'] - latest_data['Retention_Rate_For']
    st.metric(label="Latest Retention Rate", value=f"{latest_data['Retention_Rate']:.2%}", delta=f"{retention_delta:.2%} vs. Forecast")
    retention_fig = px.line(filtered_df, x='Date', y=['Retention_Rate', 'Retention_Rate_For'], labels={'value': 'Retention Rate', 'variable': 'Metric Type'}, title="Retention Rate: Actual vs. Forecast", markers=True)
    retention_fig.update_yaxes(tickformat=".2%")
    retention_fig.add_hline(y=retention_goal, line_dash="dot", annotation_text="Retention Goal", line_color="green")
    st.plotly_chart(retention_fig, use_container_width=True)

# --- ALERTS & DATA TABLE ---
st.markdown("---")
st.header("📝 Alerts Log & Raw Data")
display_df = filtered_df.set_index('Date')
st.dataframe(style_alerts_table(display_df), use_container_width=True)