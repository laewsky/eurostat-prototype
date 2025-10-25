import streamlit as st
import pandas as pd
import requests
from io import StringIO
import google.generativeai as genai
import re

# Page config
st.set_page_config(
    page_title="EU Timber Export Analyst",
    page_icon="🌲",
    layout="wide"
)

# Custom CSS - REPLACE ENTIRE SECTION
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap');
    
    :root {
        --primary-glow: #00f5ff;
        --secondary-glow: #ff00ff;
        --accent-glow: #7000ff;
        --dark-bg: #0a0a0f;
        --card-bg: rgba(20, 20, 30, 0.7);
        --glass-bg: rgba(255, 255, 255, 0.05);
    }
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Animated gradient background */
    .main {
        background: linear-gradient(135deg, #0a0a0f 0%, #1a0b2e 50%, #0f0a1e 100%);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
        position: relative;
        overflow-x: hidden;
    }
    
    .main::before {
        content: '';
        position: fixed;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: 
            radial-gradient(circle at 20% 50%, rgba(0, 245, 255, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(255, 0, 255, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 40% 20%, rgba(112, 0, 255, 0.1) 0%, transparent 50%);
        animation: floating 20s ease-in-out infinite;
        pointer-events: none;
        z-index: 0;
    }
    
    @keyframes gradientShift {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    @keyframes floating {
        0%, 100% { transform: translate(0, 0) rotate(0deg); }
        33% { transform: translate(30px, -30px) rotate(5deg); }
        66% { transform: translate(-20px, 20px) rotate(-5deg); }
    }
    
    @keyframes glow {
        0%, 100% { text-shadow: 0 0 20px var(--primary-glow), 0 0 40px var(--primary-glow); }
        50% { text-shadow: 0 0 30px var(--secondary-glow), 0 0 60px var(--secondary-glow); }
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Premium chat messages with glassmorphism */
    .chat-message {
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 1.5rem;
        display: flex;
        flex-direction: column;
        backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        position: relative;
        overflow: hidden;
        animation: slideIn 0.5s ease-out;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .chat-message::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--primary-glow), transparent);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .chat-message:hover::before {
        opacity: 1;
    }
    
    .chat-message:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 48px rgba(0, 245, 255, 0.2);
    }
    
    .chat-message.user {
        background: linear-gradient(135deg, rgba(0, 245, 255, 0.15) 0%, rgba(0, 200, 255, 0.05) 100%);
        border-left: 3px solid var(--primary-glow);
    }
    
    .chat-message.assistant {
        background: linear-gradient(135deg, rgba(255, 0, 255, 0.15) 0%, rgba(112, 0, 255, 0.05) 100%);
        border-left: 3px solid var(--secondary-glow);
    }
    
    .chat-message .message {
        margin-top: 0.75rem;
        color: #e0e0e0;
        line-height: 1.8;
        font-weight: 300;
        letter-spacing: 0.3px;
    }
    
    .chat-message .role {
        font-weight: 700;
        background: linear-gradient(135deg, var(--primary-glow), var(--secondary-glow));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    /* Animated gradient title */
    h1 {
        background: linear-gradient(135deg, #00f5ff 0%, #ff00ff 50%, #7000ff 100%);
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 900;
        font-size: 3.5rem !important;
        animation: gradientShift 8s ease infinite, glow 3s ease-in-out infinite;
        letter-spacing: -2px;
        margin-bottom: 0 !important;
    }
    
    /* Premium buttons with 3D effect */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-glow), var(--secondary-glow));
        color: white;
        border-radius: 15px;
        border: none;
        font-weight: 600;
        padding: 0.75rem 2rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        position: relative;
        overflow: hidden;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 15px rgba(112, 0, 255, 0.4);
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
        transition: left 0.5s ease;
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 8px 30px rgba(112, 0, 255, 0.6),
                    0 0 40px rgba(255, 0, 255, 0.3);
    }
    
    .stButton > button:active {
        transform: translateY(0) scale(0.98);
    }
    
    /* Premium code blocks */
    code {
        background: rgba(0, 245, 255, 0.1);
        padding: 4px 10px;
        border-radius: 8px;
        border: 1px solid rgba(0, 245, 255, 0.3);
        color: var(--primary-glow);
        font-family: 'Monaco', 'Courier New', monospace;
        font-size: 0.9em;
        box-shadow: 0 0 10px rgba(0, 245, 255, 0.2);
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 12px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(10, 10, 15, 0.5);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, var(--primary-glow), var(--secondary-glow));
        border-radius: 10px;
        border: 2px solid rgba(10, 10, 15, 0.5);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, var(--secondary-glow), var(--accent-glow));
        box-shadow: 0 0 20px rgba(255, 0, 255, 0.5);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(20, 20, 30, 0.95) 0%, rgba(10, 10, 15, 0.98) 100%);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(0, 245, 255, 0.2);
    }
    
    [data-testid="stSidebar"] h2 {
        color: var(--primary-glow);
        font-weight: 700;
        text-shadow: 0 0 20px rgba(0, 245, 255, 0.5);
    }
    
    [data-testid="stSidebar"] .element-container {
        color: #b0b0b0;
    }
    
    /* Input field styling */
    .stChatInputContainer {
        border-top: 1px solid rgba(0, 245, 255, 0.2);
        background: rgba(20, 20, 30, 0.8);
        backdrop-filter: blur(20px);
    }
    
    .stChatInput textarea {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(0, 245, 255, 0.3) !important;
        border-radius: 15px !important;
        color: #e0e0e0 !important;
        transition: all 0.3s ease;
    }
    
    .stChatInput textarea:focus {
        border-color: var(--primary-glow) !important;
        box-shadow: 0 0 20px rgba(0, 245, 255, 0.3) !important;
    }
    
    /* Success/Error messages */
    .stSuccess, .stError, .stWarning, .stInfo {
        backdrop-filter: blur(10px);
        border-radius: 12px;
        border-left-width: 3px;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        border: 1px solid rgba(0, 245, 255, 0.2);
        color: #e0e0e0;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(0, 245, 255, 0.1);
        border-color: var(--primary-glow);
        box-shadow: 0 0 15px rgba(0, 245, 255, 0.2);
    }
    
    /* Details/Summary for code blocks */
    details {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid rgba(0, 245, 255, 0.2);
        transition: all 0.3s ease;
    }
    
    details:hover {
        border-color: var(--primary-glow);
        box-shadow: 0 0 20px rgba(0, 245, 255, 0.2);
    }
    
    summary {
        cursor: pointer;
        font-weight: 600;
        color: var(--primary-glow);
        user-select: none;
        transition: all 0.3s ease;
    }
    
    summary:hover {
        color: var(--secondary-glow);
        text-shadow: 0 0 10px rgba(255, 0, 255, 0.5);
    }
    
    /* Dataframe styling */
    .dataframe {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(0, 245, 255, 0.2);
    }
    
    /* Checkbox styling */
    .stCheckbox {
        color: #e0e0e0;
    }
    
    /* Divider */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--primary-glow), transparent);
        margin: 2rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Data loading and processing
@st.cache_data(ttl=3600)
def load_and_process_data():
    """Load and process Eurostat data"""
    url = "https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/3.0/data/dataflow/ESTAT/ds-045409/1.0/*.*.*.*.*.*?c[freq]=M&c[reporter]=AT,BE,BG,CY,CZ,DE,DK,EE,ES,FI,FR,GB,GR,HR,HU,IE,IT,LT,LU,LV,MT,NL,PL,PT,RO,SE,SI,SK&c[partner]=CN,EG,SA,AE,MA,DZ,JP,KR,IN&c[product]=440711,440712,440713,440714,440719&c[flow]=2&c[indicators]=QUANTITY_IN_100KG,VALUE_IN_EUROS&c[TIME_PERIOD]=2024-01,2024-02,2024-03,2024-04,2024-05,2024-06,2024-07,2024-08,2025-01,2025-02,2025-03,2025-04,2025-05,2025-06,2025-07,2025-08&compress=false&format=csvdata&formatVersion=2.0"
    
    processing_log = []
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Read CSV
        df = pd.read_csv(StringIO(response.text))
        processing_log.append(f"Raw CSV loaded: {len(df)} rows, {len(df.columns)} columns")
        
        # Make column names case-insensitive (lowercase)
        df.columns = df.columns.str.lower()
        
        # Keep only needed columns
        needed_cols = ['reporter', 'partner', 'product', 'indicators', 'time_period', 'obs_value']
        available_cols = [col for col in needed_cols if col in df.columns]
        processing_log.append(f"Available columns: {available_cols}")
        
        df = df[available_cols]
        processing_log.append(f"After column filtering: {len(df)} rows")
        
        # Clean and standardize data
        df['reporter'] = df['reporter'].astype(str).str.strip().str.upper()
        df['partner'] = df['partner'].astype(str).str.strip().str.upper()
        df['product'] = df['product'].astype(str).str.strip()
        df['indicators'] = df['indicators'].astype(str).str.strip().str.upper()
        df['time_period'] = df['time_period'].astype(str).str.strip()
        df['obs_value'] = pd.to_numeric(df['obs_value'], errors='coerce').fillna(0)
        
        # Remove any rows with missing critical data
        before_dropna = len(df)
        df = df.dropna(subset=['reporter', 'partner', 'product', 'indicators', 'time_period'])
        after_dropna = len(df)
        processing_log.append(f"Dropped {before_dropna - after_dropna} rows with missing data")
        processing_log.append(f"After cleaning: {len(df)} rows")
        
        # Product multipliers for CUM_VALUE calculation
        multipliers = {
            '440711': 0.1888,
            '440712': 0.2128,
            '440713': 0.2,
            '440714': 0.2,
            '440719': 0.2
        }
        
        # Add CUM_VALUE rows (cubic meters)
        quantity_rows = df[df['indicators'] == 'QUANTITY_IN_100KG'].copy()
        processing_log.append(f"Found {len(quantity_rows)} QUANTITY_IN_100KG rows")
        
        quantity_rows['indicators'] = 'CUM_VALUE'
        quantity_rows['obs_value'] = quantity_rows.apply(
            lambda row: row['obs_value'] * multipliers.get(str(row['product']), 0.2),
            axis=1
        )
        
        # Concatenate to have CUM_VALUE available
        df = pd.concat([df, quantity_rows], ignore_index=True)
        processing_log.append(f"After adding CUM_VALUE: {len(df)} rows")
        
        # Add UNIT_VALUE rows (price per cubic meter)
        value_rows = df[df['indicators'] == 'VALUE_IN_EUROS'].copy()
        processing_log.append(f"Found {len(value_rows)} VALUE_IN_EUROS rows")
        
        unit_value_rows = []
        skipped_count = 0
        
        for _, value_row in value_rows.iterrows():
            # Find corresponding CUM_VALUE
            cum_value_row = df[
                (df['reporter'] == value_row['reporter']) &
                (df['partner'] == value_row['partner']) &
                (df['product'] == value_row['product']) &
                (df['time_period'] == value_row['time_period']) &
                (df['indicators'] == 'CUM_VALUE')
            ]
            
            new_row = value_row.copy()
            new_row['indicators'] = 'UNIT_VALUE'
            
            if cum_value_row.empty or cum_value_row.iloc[0]['obs_value'] == 0:
                # Set to NaN/0 instead of skipping
                new_row['obs_value'] = 0  # or use float('nan')
                skipped_count += 1
            else:
                new_row['obs_value'] = value_row['obs_value'] / cum_value_row.iloc[0]['obs_value']
            
            unit_value_rows.append(new_row)
        
        if unit_value_rows:
            df = pd.concat([df, pd.DataFrame(unit_value_rows)], ignore_index=True)
            processing_log.append(f"Added {len(unit_value_rows)} UNIT_VALUE rows ({skipped_count} with zero/missing volume)")
            
        return df
    
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        if processing_log:
            st.error(f"Processing log: {processing_log}")
        return None
        
# System prompt for Gemini
SYSTEM_PROMPT = """You are a helpful analyst who addresses the statistics database for EU softwood timber exports to global countries in order to answer user's queries. Your knowledge is limited outside this database.

When asked, you think first meticulously which rows and cells to look at, and construct a short Python code snippet that will query the dataframe 'df'.

Country labels (Reporter - use uppercase codes):
AT=Austria, BE=Belgium, BG=Bulgaria, CY=Cyprus, CZ=Czech Republic, DE=Germany, DK=Denmark, EE=Estonia, ES=Spain, FI=Finland, FR=France, GB=United Kingdom, GR=Greece, HR=Croatia, HU=Hungary, IE=Ireland, IT=Italy, LT=Lithuania, LU=Luxembourg, LV=Latvia, MT=Malta, NL=Netherlands, PL=Poland, PT=Portugal, RO=Romania, SE=Sweden, SI=Slovenia, SK=Slovakia

Species labels (Product - use as strings):
440711=pine, 440712=spruce and fir, 440713=SPF, 440714=hemlock and fir, 440719=other softwoods

Importing country labels (Partner - use uppercase codes):
CN=China, EG=Egypt, SA=Saudi Arabia, AE=UAE, MA=Morocco, DZ=Algeria, JP=Japan, KR=South Korea, IN=India

Indicators (use uppercase):
- QUANTITY_IN_100KG: Export quantity in 100kg units
- VALUE_IN_EUROS: Export value in euros
- CUM_VALUE: Cubic meters (calculated from quantity)
- UNIT_VALUE: Price per cubic meter in EUR/m³ (calculated from value/volume)

The database has stats for all EU countries, all softwood lumber species, exports volume and value to China, Top-5 MENA countries, India, Japan, South Korea; monthly from January 2024 to August 2025.

DataFrame columns: reporter, partner, product, indicators, time_period, obs_value

IMPORTANT INSTRUCTIONS:
1. Generate concise Python code using pandas operations on 'df'
2. Assign results to a variable called 'result'
3. Use uppercase for reporter, partner, and indicators when filtering
4. Use string format for product codes (e.g., '440711')
5. When interpreting results, use ONLY the actual executed result - never make up numbers
6. If data is missing or you can't answer, say so clearly
7. When asked about imports or import volumes (and value or tons not mentioned), by default answer about m³ and change only if corrected by user

Example code:
```result = df[(df['reporter'] == 'DE') & (df['indicators'] == 'CUM_VALUE') & (df['partner'] == 'CN')]['obs_value'].sum()```
"""

# Initialize Gemini
@st.cache_resource
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        st.error("⚠️ Please add GEMINI_API_KEY to your Streamlit secrets!")
        st.stop()
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-pro')

# Execute code safely
def execute_code(code_str, df):
    """Safely execute code generated by AI"""
    try:
        local_vars = {'df': df, 'pd': pd}
        exec(code_str, {"__builtins__": {}}, local_vars)
        if 'result' in local_vars:
            return local_vars['result']
        return None
    except Exception as e:
        return f"⚠️ Error executing code: {str(e)}"

# Process AI response
def process_ai_response(response_text, df):
    """Extract and execute code from AI response"""
    # Find Python code blocks
    code_blocks = re.findall(r'```python\n(.*?)\n```', response_text, re.DOTALL)
    
    formatted_response = response_text
    
    for code in code_blocks:
        result = execute_code(code, df)
        if result is not None and isinstance(result, (int, float)):
            # Format the result properly
            try:
                if isinstance(result, float):
                    formatted_result = f"{result:,.2f}"
                else:
                    formatted_result = f"{result:,}"
                
                # Replace code block with collapsible version
                formatted_response = formatted_response.replace(
                    f"```python\n{code}\n```",
                    f"<details><summary>📊 View query code</summary>\n\n```python\n{code}\n```\n</details>\n\n💡 **Result:** `{formatted_result}`"
                )
            except:
                pass
    
    return formatted_response
    
# Initialize session state
if 'df' not in st.session_state:
    with st.spinner('📥 Loading Eurostat data...'):
        st.session_state.df = load_and_process_data()

if 'model' not in st.session_state:
    st.session_state.model = init_gemini()

if 'messages' not in st.session_state:
    st.session_state.messages = []

# UI Layout
st.title("🌲 EU Timber Export Analyst")
st.markdown("<p style='color: rgba(255,255,255,0.6); font-size: 1.1rem; font-weight: 300; margin-top: -1rem; letter-spacing: 1px;'>⚡ Powered by Gemini 2.5 Pro | 🌍 Real-time Eurostat COMEXT Data</p>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("📊 Database Coverage")
    st.markdown("""
    **Geographic Coverage:**
    - 🇪🇺 All EU-27 + UK
    - 🌍 9 partner countries
    
    **Products:**
    - 🌲 Pine (440711)
    - 🌲 Spruce & Fir (440712)
    - 🌲 SPF (440713)
    - 🌲 Hemlock & Fir (440714)
    - 🌲 Other softwoods (440719)
    
    **Period:**
    - 📅 Jan 2024 - Aug 2025
    - 📊 Monthly data
    
    **Metrics:**
    - Volume (100kg, m³)
    - Value (EUR)
    - Unit prices (EUR/m³)
    """)
    
    if st.session_state.df is not None:
        st.success(f"✅ {len(st.session_state.df):,} records loaded")
        
        # Enhanced data preview toggle
        if st.checkbox("🔍 Show data details"):
            
            # Check for any issues
            with st.expander("⚠️ Data Quality Check"):
                st.write(f"**Missing values:**")
                missing = st.session_state.df.isnull().sum()
                st.dataframe(missing[missing > 0] if missing.sum() > 0 else pd.Series({"No missing values": 0}))
                
                st.write(f"**Zero values in obs_value:**")
                zero_count = len(st.session_state.df[st.session_state.df['obs_value'] == 0])
                st.write(f"{zero_count:,} rows ({zero_count/len(st.session_state.df)*100:.1f}%)")
                
                st.write(f"**Negative values in obs_value:**")
                neg_count = len(st.session_state.df[st.session_state.df['obs_value'] < 0])
                st.write(f"{neg_count:,} rows")

    # Show processing log
            with st.expander("🔧 Data Processing Log"):
                if hasattr(st.session_state, 'processing_log'):
                    for log_entry in st.session_state.processing_log:
                        st.text(log_entry)
                else:
                    st.info("No processing log available")
    # Show skipped UNIT_VALUE calculations
            if hasattr(st.session_state, 'skipped_unit_values') and st.session_state.skipped_unit_values:
                with st.expander(f"⚠️ Skipped UNIT_VALUE ({len(st.session_state.skipped_unit_values)})"):
                    st.warning(f"Could not calculate UNIT_VALUE for {len(st.session_state.skipped_unit_values)} record(s)")
                    for idx, record in enumerate(st.session_state.skipped_unit_values, 1):
                        st.write(f"**Record {idx}:**")
                        st.json(record)
                        
                        # Show the actual data for this record
                        if st.session_state.df is not None:
                            related = st.session_state.df[
                                (st.session_state.df['reporter'] == record.get('reporter')) &
                                (st.session_state.df['partner'] == record.get('partner')) &
                                (st.session_state.df['product'] == record.get('product')) &
                                (st.session_state.df['time_period'] == record.get('time_period'))
                            ]
                            if not related.empty:
                                st.dataframe(related)
                                
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.session_state.df = load_and_process_data()
            st.rerun()
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
            
# Chat messages
for message in st.session_state.messages:
    role_class = "user" if message["role"] == "user" else "assistant"
    role_icon = "👤" if message["role"] == "user" else "🤖"
    
    st.markdown(f"""
        <div class="chat-message {role_class}">
            <div class="role">{role_icon} {message["role"].title()}</div>
            <div class="message">{message["content"]}</div>
        </div>
    """, unsafe_allow_html=True)

# Welcome message - REPLACE THE WELCOME MESSAGE SECTION
if not st.session_state.messages:
    st.markdown("""
        <div class="chat-message assistant">
            <div class="role">🤖 AI Assistant</div>
            <div class="message">
                <strong style="font-size: 1.1em; color: var(--primary-glow);">Welcome to the Future of Timber Analytics</strong>
                <br><br>
                I'm your premium EU Timber Export Analyst, powered by advanced AI. Ready to unlock insights from millions of data points.
                <br><br>
                <b style="color: var(--secondary-glow);">🎯 Try these power queries:</b>
                <ul style="line-height: 2; margin-top: 0.5rem;">
                    <li>💎 "What are Germany's total pine exports to China in 2024?"</li>
                    <li>📊 "Which EU country exported the most spruce to Egypt?"</li>
                    <li>💰 "Show me average unit prices for Finnish exports to Japan"</li>
                    <li>⚡ "Compare Swedish and Austrian exports to Saudi Arabia"</li>
                    <li>📈 "What's the trend for Poland's exports in 2024?"</li>
                </ul>
            </div>
        </div>
    """, unsafe_allow_html=True)

# Chat input
if prompt := st.chat_input("💬 Ask about timber exports..."):
    if st.session_state.df is None:
        st.error("❌ Data not loaded. Please refresh the page.")
        st.stop()
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    st.markdown(f"""
        <div class="chat-message user">
            <div class="role">👤 User</div>
            <div class="message">{prompt}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Generate AI response
    with st.spinner("🔍 Analyzing data..."):
        try:
            chat = st.session_state.model.start_chat(history=[])
            
            # Step 1: Get code from AI
            code_prompt = f"""{SYSTEM_PROMPT}

User question: {prompt}

Generate ONLY the Python code to answer this question. Do not include explanations yet.
Assign the final result to a variable called 'result'.
"""
            code_response = chat.send_message(code_prompt)
            
            # Step 2: Extract and execute code
            code_blocks = re.findall(r'```python\n(.*?)\n```', code_response.text, re.DOTALL)
            
            if code_blocks:
                code = code_blocks[0]
                execution_result = execute_code(code, st.session_state.df)
                
                # Step 3: Ask AI to formulate response using ACTUAL result
                interpretation_prompt = f"""The code executed successfully and returned this result: {execution_result}

User's question was: {prompt}

Now provide a clear, natural language answer using this EXACT result. Include:
1. A direct answer to the question
2. The actual number from the result: {execution_result}
3. Appropriate units and context
4. Do NOT make up any numbers - use only the result provided: {execution_result}

Keep it concise and professional."""
                
                final_response = chat.send_message(interpretation_prompt)
                
                # Format final output
                if isinstance(execution_result, (int, float)):
                    if isinstance(execution_result, float):
                        formatted_result = f"{execution_result:,.2f}"
                    else:
                        formatted_result = f"{execution_result:,}"
                else:
                    formatted_result = str(execution_result)
                
                full_response = f"""<details><summary>📊 View query code</summary>

```python
{code}
```
</details>

💡 **Result:** `{formatted_result}`

{final_response.text}"""
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            else:
                # No code generated - direct response
                direct_response = chat.send_message(f"{SYSTEM_PROMPT}\n\nUser question: {prompt}")
                st.session_state.messages.append({"role": "assistant", "content": direct_response.text})
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    st.rerun()
