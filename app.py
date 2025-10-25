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

# Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #f5f7fa;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #e3f2fd;
        border-left: 5px solid #2196F3;
    }
    .chat-message.assistant {
        background-color: #f1f8e9;
        border-left: 5px solid #8bc34a;
    }
    .chat-message .message {
        margin-top: 0.5rem;
        color: #333;
        line-height: 1.6;
    }
    .chat-message .role {
        font-weight: 600;
        color: #555;
        font-size: 0.9rem;
    }
    h1 {
        color: #1976d2;
        font-weight: 700;
    }
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        border: none;
        font-weight: 500;
    }
    .stButton > button:hover {
        background-color: #45a049;
    }
    code {
        background-color: #f4f4f4;
        padding: 2px 6px;
        border-radius: 3px;
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
st.markdown("*Powered by Gemini 2.5 Pro | Data from Eurostat COMEXT*")

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

# Welcome message
if not st.session_state.messages:
    st.markdown("""
        <div class="chat-message assistant">
            <div class="role">🤖 Assistant</div>
            <div class="message">
                Hello! I'm your EU Timber Export Analyst. I can help you analyze softwood timber export statistics from EU countries to major global markets.
                <br><br>
                <b>Try asking:</b>
                <ul>
                    <li>"What are Germany's total pine exports to China in 2024?"</li>
                    <li>"Which EU country exported the most spruce to Egypt?"</li>
                    <li>"Show me average unit prices for Finnish exports to Japan"</li>
                    <li>"Compare Swedish and Austrian exports to Saudi Arabia"</li>
                    <li>"What's the trend for Poland's exports in 2024?"</li>
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
