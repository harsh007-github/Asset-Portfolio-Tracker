import streamlit as st
import requests
import pandas as pd
import plotly.express as px
st.set_page_config(page_title="Asset Portfolio Tracker", layout="wide")
st.title("Real-Time Asset Portfolio Tracker")

if "portfolio" not in st.session_state:
    st.session_state.portfolio = {} 

@st.cache_data(ttl=60)  
def fetch_live_prices():
    """Fetches real-time cryptocurrency price data using a public REST API."""
    url = "https://min-api.cryptocompare.com/data/pricemultifull?fsyms=BTC,ETH,SOL,BNB&tsyms=USD"
    try:
        response = requests.get(url)
        response.raise_for_status()  
        data = response.json()
        
        raw_prices = data.get("RAW", {})
        processed_prices = {}
        for asset in ["BTC", "ETH", "SOL", "BNB"]:
            processed_prices[asset] = {
                "price": raw_prices.get(asset, {}).get("USD", {}).get("PRICE", 0.0),
                "change_24h": raw_prices.get(asset, {}).get("USD", {}).get("CHANGEPCT24HOUR", 0.0)
            }
        return processed_prices
    except Exception as e:
        st.error("Failed to connect to the live price API.")
        return {"BTC": {"price": 65000.0, "change_24h": 0.0}, "ETH": {"price": 3500.0, "change_24h": 0.0},
                "SOL": {"price": 150.0, "change_24h": 0.0}, "BNB": {"price": 580.0, "change_24h": 0.0}}

live_market = fetch_live_prices()

st.sidebar.header("Manage Portfolio")
asset_choice = st.sidebar.selectbox("Select Asset", ["BTC", "ETH", "SOL", "BNB"])
asset_quantity = st.sidebar.number_input("Quantity Held", min_value=0.0, step=0.01, value=0.0)

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.sidebar.button("Update/Add Asset"):
        if asset_quantity > 0:
            st.session_state.portfolio[asset_choice] = asset_quantity
            st.toast(f"Updated {asset_choice} balance!")
            st.rerun()

with col2:
    if st.sidebar.button("Clear Asset"):
        if asset_choice in st.session_state.portfolio:
            del st.session_state.portfolio[asset_choice]
            st.toast(f"Removed {asset_choice} from portfolio")
            st.rerun()

if not st.session_state.portfolio:
    st.info("Your portfolio is currently empty. Use the sidebar menu to add holdings.")
else:
    portfolio_rows = []
    total_portfolio_value = 0.0
    
    for asset, quantity in st.session_state.portfolio.items():
        live_price = live_market[asset]["price"]
        current_value = quantity * live_price
        total_portfolio_value += current_value
        
        portfolio_rows.append({
            "Asset": asset,
            "Quantity": quantity,
            "Live Price ($)": round(live_price, 2),
            "Current Value ($)": round(current_value, 2),
            "24h Change (%)": round(live_market[asset]["change_24h"], 2)
        })
    df = pd.DataFrame(portfolio_rows)
    st.subheader("Portfolio Performance Overview")
    st.metric(
        label="Total Portfolio Asset Net Worth", 
        value=f"${total_portfolio_value:,.2f}",
        delta="Live Tracking Active"
    )
    
    st.markdown("---")
    
    left_ui, right_ui = st.columns([3, 2])
    
    with left_ui:
        st.write("### Current Holdings Summary")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
    with right_ui:
        st.write("### Asset Distribution Allocation")
        fig = px.pie(df, values="Current Value ($)", names="Asset", hole=0.4,
                     color_discrete_sequence=px.colors.sequential.RdBu)
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)
