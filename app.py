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
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700;900&family=Vollkorn:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');
    
    :root {
        --forest-deep: #1a3a2e;
        --forest-mid: #2d5a47;
        --sage: #8b9d83;
        --cream: #f4f1ea;
        --charcoal: #2b2d2f;
        --gold: #c9a96e;
        --timber: #6b4423;
        --accent: #4a7c59;
    }
    
    * {
        font-family: 'Vollkorn', serif;
    }
    
    /* Sophisticated background */
    .main {
        background-color: var(--cream);
        background-image: 
            linear-gradient(90deg, rgba(139, 157, 131, 0.03) 1px, transparent 1px),
            linear-gradient(rgba(139, 157, 131, 0.03) 1px, transparent 1px);
        background-size: 60px 60px;
        position: relative;
    }
    
    .main::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: radial-gradient(circle at 20% 20%, rgba(74, 124, 89, 0.04) 0%, transparent 50%),
                    radial-gradient(circle at 80% 80%, rgba(107, 68, 35, 0.04) 0%, transparent 50%);
        pointer-events: none;
        z-index: 0;
    }
    
    /* Elegant chat messages */
    .chat-message {
        padding: 2rem 2.5rem;
        border-radius: 2px;
        margin-bottom: 2rem;
        display: flex;
        flex-direction: column;
        position: relative;
        background: white;
        box-shadow: 
            0 1px 3px rgba(0,0,0,0.06),
            0 8px 24px rgba(0,0,0,0.08);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        border-top: 3px solid var(--gold);
        opacity: 0;
        animation: fadeInUp 0.6s ease-out forwards;
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .chat-message:hover {
        transform: translateY(-2px);
        box-shadow: 
            0 4px 6px rgba(0,0,0,0.07),
            0 12px 40px rgba(0,0,0,0.12);
    }
    
    .chat-message.user {
        background: linear-gradient(to bottom, #ffffff 0%, #fafaf8 100%);
        border-top-color: var(--accent);
        border-left: 1px solid var(--accent);
    }
    
    .chat-message.assistant {
        background: linear-gradient(to bottom, #ffffff 0%, #f9f8f4 100%);
        border-top-color: var(--timber);
        border-left: 1px solid var(--sage);
    }
    
    .chat-message::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 2.5rem;
        right: 2.5rem;
        height: 1px;
        background: linear-gradient(to right, transparent, var(--sage), transparent);
        opacity: 0.3;
    }
    
    .chat-message .message {
        margin-top: 1rem;
        color: var(--charcoal);
        line-height: 1.8;
        font-weight: 500;
        font-size: 1.05rem;
        letter-spacing: 0.01em;
    }
    
    .chat-message .role {
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 500;
        color: var(--forest-deep);
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        opacity: 0.7;
        position: relative;
        display: inline-block;
        padding-bottom: 0.5rem;
    }
    
    .chat-message .role::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 30px;
        height: 2px;
        background: var(--gold);
    }
    
    /* Playfair Display for headlines */
    h1 {
        font-family: 'Playfair Display', serif !important;
        color: var(--forest-deep) !important;
        font-weight: 700 !important;
        font-size: 4rem !important;
        letter-spacing: -0.02em !important;
        margin-bottom: 0.5rem !important;
        line-height: 1.1 !important;
        position: relative;
        display: inline-block;
    }
    
    h1::after {
        content: '';
        position: absolute;
        bottom: -10px;
        left: 0;
        width: 80px;
        height: 4px;
        background: linear-gradient(to right, var(--gold), var(--timber));
    }
    
    /* Refined buttons */
    .stButton > button {
        background: var(--forest-deep);
        color: var(--cream);
        border-radius: 0;
        border: none;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 500;
        padding: 0.75rem 2rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-size: 0.75rem;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(26, 58, 46, 0.3);
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(201, 169, 110, 0.3), transparent);
        transition: left 0.6s ease;
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:hover {
        background: var(--forest-mid);
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(26, 58, 46, 0.4);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Sophisticated code blocks */
    code {
        background: rgba(26, 58, 46, 0.06);
        padding: 3px 8px;
        border-radius: 2px;
        border-left: 2px solid var(--gold);
        color: var(--timber);
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.9em;
        font-weight: 500;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--cream);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--sage);
        border-radius: 0;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--forest-mid);
    }
    
    /* Sidebar - editorial style */
    [data-testid="stSidebar"] {
        background: var(--forest-deep);
        background-image: 
            linear-gradient(rgba(201, 169, 110, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(201, 169, 110, 0.03) 1px, transparent 1px);
        background-size: 40px 40px;
        border-right: 3px solid var(--gold);
    }
    
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        font-family: 'Playfair Display', serif;
        color: var(--cream);
        font-weight: 600;
        border-bottom: 1px solid var(--gold);
        padding-bottom: 0.5rem;
    }
    
    [data-testid="stSidebar"] .element-container {
        color: var(--cream);
        opacity: 0.9;
    }
    
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] li {
        font-size: 0.95rem;
        line-height: 1.7;
    }
    
    /* Input field - elegant */
    .stChatInputContainer {
        border-top: 2px solid var(--sage);
        background: white;
    }
    
    .stChatInput textarea {
        background: white !important;
        border: 2px solid var(--sage) !important;
        border-radius: 0 !important;
        color: var(--charcoal) !important;
        font-family: 'Vollkorn', serif !important;
        font-size: 1.05rem !important;
        transition: all 0.3s ease;
    }
    
    .stChatInput textarea:focus {
        border-color: var(--forest-deep) !important;
        box-shadow: inset 0 2px 8px rgba(26, 58, 46, 0.1) !important;
    }
    
    /* Success/Info messages - refined */
    .stSuccess {
        background: rgba(74, 124, 89, 0.1);
        border-left: 3px solid var(--accent);
        border-radius: 0;
        color: var(--forest-deep);
    }
    
    .stError {
        background: rgba(139, 69, 19, 0.1);
        border-left: 3px solid var(--timber);
        border-radius: 0;
    }
    
    /* Expander - minimal */
    .streamlit-expanderHeader {
        background: rgba(139, 157, 131, 0.08);
        border-radius: 0;
        border-left: 2px solid var(--gold);
        color: var(--forest-deep);
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.85rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(139, 157, 131, 0.15);
        border-left-color: var(--timber);
    }
    
    /* Details/Summary - elegant reveal */
    details {
        background: rgba(244, 241, 234, 0.5);
        border-radius: 0;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border-left: 3px solid var(--sage);
        transition: all 0.3s ease;
    }
    
    details:hover {
        background: rgba(244, 241, 234, 0.8);
        border-left-color: var(--gold);
    }
    
    summary {
        cursor: pointer;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 500;
        color: var(--forest-deep);
        font-size: 0.9rem;
        user-select: none;
        letter-spacing: 0.05em;
    }
    
    summary:hover {
        color: var(--timber);
    }
    
    /* Divider - subtle and classy */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(to right, transparent, var(--sage), transparent);
        margin: 2.5rem 0;
        opacity: 0.4;
    }
    
    /* Typography refinements */
    strong, b {
        color: var(--forest-deep);
        font-weight: 600;
    }
    
    ul {
        list-style: none;
        padding-left: 0;
    }
    
    ul li::before {
        content: "▪";
        color: var(--gold);
        font-weight: bold;
        display: inline-block;
        width: 1.5em;
        margin-left: -1.5em;
    }
    
    /* Dataframe styling */
    .dataframe {
        border: 1px solid var(--sage);
        border-radius: 0;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.9rem;
    }
    
    /* Smooth transitions for interactive elements */
    a, button, summary, .streamlit-expanderHeader {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    </style>
    """, unsafe_allow_html=True)

# JavaScript enhancements - ADD THIS NEW SECTION
st.components.v1.html("""
    <script>
    // Smooth scroll reveal animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe all chat messages
    setTimeout(() => {
        document.querySelectorAll('.chat-message').forEach(el => {
            observer.observe(el);
        });
    }, 100);
    
    // Parallax effect for background
    let ticking = false;
    window.addEventListener('scroll', () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                const scrolled = window.pageYOffset;
                const parallax = document.querySelector('.main::before');
                if (parallax) {
                    parallax.style.transform = `translateY(${scrolled * 0.3}px)`;
                }
                ticking = false;
            });
            ticking = true;
        }
    });
    
    // Magnetic effect for buttons
    document.addEventListener('mousemove', (e) => {
        document.querySelectorAll('.stButton > button').forEach(button => {
            const rect = button.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;
            const distance = Math.sqrt(x * x + y * y);
            
            if (distance < 100) {
                const strength = (100 - distance) / 100;
                button.style.transform = `translate(${x * strength * 0.2}px, ${y * strength * 0.2}px)`;
            } else {
                button.style.transform = 'translate(0, 0)';
            }
        });
    });
    
    // Typing indicator for AI responses
    function typeWriter(element, text, speed = 30) {
        let i = 0;
        element.innerHTML = '';
        const timer = setInterval(() => {
            if (i < text.length) {
                element.innerHTML += text.charAt(i);
                i++;
            } else {
                clearInterval(timer);
            }
        }, speed);
    }
    
    // Add subtle particle effect on data reveals
    function createParticle(x, y) {
        const particle = document.createElement('div');
        particle.style.cssText = `
            position: fixed;
            left: ${x}px;
            top: ${y}px;
            width: 4px;
            height: 4px;
            background: #c9a96e;
            border-radius: 50%;
            pointer-events: none;
            z-index: 9999;
            animation: particleFade 1s ease-out forwards;
        `;
        document.body.appendChild(particle);
        setTimeout(() => particle.remove(), 1000);
    }
    
    // Add particle animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes particleFade {
            0% { opacity: 1; transform: translateY(0) scale(1); }
            100% { opacity: 0; transform: translateY(-50px) scale(0); }
        }
    `;
    document.head.appendChild(style);
    
    // Trigger particles on code execution
    document.addEventListener('click', (e) => {
        if (e.target.tagName === 'SUMMARY') {
            for (let i = 0; i < 5; i++) {
                setTimeout(() => {
                    createParticle(
                        e.clientX + (Math.random() - 0.5) * 50,
                        e.clientY + (Math.random() - 0.5) * 50
                    );
                }, i * 50);
            }
        }
    });
    </script>
""", height=0)

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
SYSTEM_PROMPT = """You're a top-notch, seasoned industry analyst with excellent analytic skills, logic and journalistic, neutral style. You work with us as a helpful analyst who addresses the statistics database for EU softwood timber exports to global countries in order to answer user's queries. Your knowledge is limited outside this database.

You're very clever, thoughtful and reflect multi-directionally. When asked, you think first meticulously which rows and cells to look at, and construct a short Python code snippet that will query the dataframe 'df'.

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
st.markdown("<p style='font-family: \"IBM Plex Mono\", monospace; color: #6b4423; font-size: 0.85rem; font-weight: 500; margin-top: -1rem; letter-spacing: 0.1em; text-transform: uppercase;'>Powered by Gemini 2.5 Pro • Eurostat COMEXT</p>", unsafe_allow_html=True)

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

# Welcome message - REPLACE
if not st.session_state.messages:
    st.markdown("""
        <div class="chat-message assistant">
            <div class="role">AI Analyst</div>
            <div class="message">
                <strong style="font-family: 'Playfair Display', serif; font-size: 1.3em; color: var(--forest-deep);">Welcome to EU Timber Export Intelligence</strong>
                <br><br>
                I provide sophisticated analysis of softwood timber export statistics across European markets. Ask me anything about trade flows, pricing dynamics, or market trends.
                <br><br>
                <b style="color: var(--timber);">Sample inquiries:</b>
                <ul style="margin-top: 0.5rem;">
                    <li>What are Germany's total pine exports to China in 2024?</li>
                    <li>Which EU country exported the most spruce to Egypt?</li>
                    <li>Show me average unit prices for Finnish exports to Japan</li>
                    <li>Compare Swedish and Austrian exports to Saudi Arabia</li>
                    <li>What's the trend for Poland's exports in 2024?</li>
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
3. Appropriate units and context. Be precise, but narrative: remember you're a top-notch analyst with excellent editorial skills and well-developed logic. Your user is likely well-familiar with timber market and wants data-driven insights.
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
