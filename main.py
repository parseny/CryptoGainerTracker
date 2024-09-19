import streamlit as st
import pandas as pd
import plotly.express as px
import logging
import os
from pathlib import Path
from api_helpers import fetch_crypto_data, fetch_zapper_data, fetch_crypto_news, fetch_fear_greed_index
from data_processing import process_crypto_data, filter_crypto_data, get_top_gainers
from visualization import create_price_chart
from similarity_algorithm import find_similar_coins
from constants import COIN_TYPES

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

st.set_page_config(page_title="Crypto Tracker", layout="wide")

# Load custom CSS
css_file = Path(__file__).parent / "style.css"
with open(css_file) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Main application
def main():
    logging.info("Starting main() function")
    try:
        st.title("Cryptocurrency Tracking Application")

        # Add a loading indicator
        with st.spinner("Loading cryptocurrency data..."):
            logging.info("Starting data fetch...")
            # Fetch and process data
            crypto_data = fetch_crypto_data()
            logging.info(f"Fetched {len(crypto_data)} cryptocurrencies")

            logging.info("Processing crypto data...")
            df = process_crypto_data(crypto_data)
            logging.info(f"Processed {len(df)} valid cryptocurrencies")

        # Sidebar filters
        st.sidebar.header("Filters")
        selected_types = st.sidebar.multiselect("Select Coin Types", COIN_TYPES, default=COIN_TYPES)
        min_price = st.sidebar.number_input("Minimum Price ($)", min_value=0.0, value=0.0)
        max_price = st.sidebar.number_input("Maximum Price ($)", min_value=0.0, value=1000000.0)
        min_market_cap = st.sidebar.number_input("Minimum Market Cap ($)", min_value=0, value=0)

        logging.info("Applying filters...")
        # Apply filters
        filtered_df = filter_crypto_data(df, selected_types, min_price, max_price, min_market_cap)
        logging.info(f"Filtered to {len(filtered_df)} cryptocurrencies")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.header("Cryptocurrency List")
            if not filtered_df.empty:
                st.dataframe(filtered_df[['name', 'symbol', 'price', 'market_cap', '24h_change', 'type']])
            else:
                st.warning("No cryptocurrencies match the current filters.")

            logging.info("Calculating top gainers...")
            st.header("Top Gainers (24h)")
            top_gainers = get_top_gainers(df)
            if not top_gainers.empty:
                st.dataframe(top_gainers[['name', 'symbol', 'price', 'market_cap', '24h_change']])
            else:
                st.warning("No top gainers found.")

        with col2:
            st.header("Fear & Greed Index")
            fng_data = fetch_fear_greed_index()
            if fng_data:
                st.metric("Fear & Greed Index", fng_data['value'], fng_data['value_classification'])
            else:
                st.warning("Unable to fetch Fear & Greed Index at the moment.")

            st.header("Latest Crypto News")
            news_items = fetch_crypto_news()
            if news_items:
                for item in news_items:
                    st.subheader(item['title'])
                    st.write(f"Source: {item['source']}")
                    st.write(item['body'][:200] + "...")  # Display first 200 characters of the news body
                    st.write(f"[Read more]({item['url']})")
                    st.write("---")
            else:
                st.warning("Unable to fetch crypto news at the moment.")

        st.header("Similar Coin Recommendations")
        if not top_gainers.empty:
            selected_gainer = st.selectbox("Select a top gainer for recommendations", top_gainers['name'])
            if selected_gainer:
                selected_coin = df[df['name'] == selected_gainer].iloc[0]
                logging.info(f"Selected coin: {selected_coin['name']}")
                similar_coins = find_similar_coins(selected_coin, df)
                logging.info(f"Found {len(similar_coins)} similar coins")
                if not similar_coins.empty:
                    st.dataframe(similar_coins[['name', 'symbol', 'price', 'market_cap', '24h_change']])
                else:
                    st.write("No similar coins found.")

                # Price chart for selected coin
                st.header(f"Price Chart: {selected_gainer}")
                logging.info(f"Creating price chart for {selected_gainer}")
                chart = create_price_chart(selected_coin)
                st.plotly_chart(chart)
        else:
            st.warning("No top gainers available for recommendations.")

        logging.info("Application finished loading")
    except Exception as e:
        logging.error(f"An error occurred in main(): {str(e)}")
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    logging.info(f"COINMARKETCAP_API_KEY is {'set' if os.environ.get('COINMARKETCAP_API_KEY') else 'not set'}")
    logging.info(f"ZAPPER_API_KEY is {'set' if os.environ.get('ZAPPER_API_KEY') else 'not set'}")
    main()
