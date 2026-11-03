
import json
import re
from collections import Counter
from typing import Dict, List, Tuple

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

try:
    import spacy
    from spacy.tokens import Token
except Exception:
    spacy = None

st.set_page_config(
    page_title="SEMANTIX | Semantic Interpretation Lab",
    page_icon="✳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------- Design system -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
:root {
  --ink:#33443f; --muted:#718078; --paper:#f7f6f1; --sage:#dce9e1;
  --lav:#e9e2f0; --blue:#e1ebf1; --peach:#f3e5da; --line:#e5e5dc;
}
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background:var(--paper); color:var(--ink); }
[data-testid="stSidebar"] { background:#eef1eb; border-right:1px solid #e0e5dc; }
h1,h2,h3 { color:var(--ink)!important; }
h1 { font-family:'Playfair Display',serif!important; letter-spacing:-.7px; }
.hero {
 background:linear-gradient(115deg,#e6eee7 0%,#eee8f1 55%,#f3e8df 100%);
 border:1px solid #e3e5dc; border-radius:22px; padding:28px 30px; margin:4px 0 22px;
}
.eyebrow { text-transform:uppercase; letter-spacing:2px; color:#718078; font-size:11px; font-weight:700; }
.hero h1 { font-size:42px; margin:8px 0 6px; }
.hero p { color:#62736b; font-size:15px; max-width:760px; margin:0; }
.module-card { border:1px solid var(--line); background:#fffefa; border-radius:16px; padding:18px; min-height:132px; }
.module-card h3 { font-size:17px; margin:8px 0 4px; }
.module-card p { color:#718078; font-size:13px; margin:0; }
.kpi { background:#fffefa; border:1px solid var(--line); border-radius:14px; padding:16px 18px; }
.kpi-label { color:#758179; font-size:11px; text-transform:uppercase; letter-spacing:1.2px; }
.kpi-value { color:#33443f; font-size:24px; font-weight:700; margin-top:4px; }
.note { background:#edf2ed; border-left:4px solid #8da998; padding:12px 15px; border-radius:8px; color:#53675b; font-size:13px; }
.soft { color:#758179; font-size:13px; }
div.stButton > button { border-radius:10px; border:1px solid #c9d5cc; background:#dce9e1; color:#33443f; font-weight:700; }
div.stButton > button:hover { border-color:#8ca795; color:#263b32; background:#d1e1d6; }
.stDownloadButton button { border-radius:10px; }
hr { border-color:#e4e5dd; }
</style>
""", unsafe_allow_html=True)

# ----------------------------- NLP engine -----------------------------
SENSES = {
    "bank": [
        {"name":"Financial institution", "definition":"an organization that accepts deposits, keeps money safe, and provides loans or financial services",
         "keywords":["money","deposit","withdraw","account","loan","cash","credit","savings","branch","finance"]},
        {"name":"Land beside a river", "definition":"the sloping land alongside a river or stream",
         "keywords":["river","water","stream","shore","fisherman","fishing","flow","edge","boat"]},
        {"name":"A set or reserve", "definition":"a supply or reserve of something available for use",
         "keywords":["blood","memory","data","cloud","resource","reserve","storage"]},
    ],
    "bat": [
        {"name":"Flying mammal", "definition":"a nocturnal mammal with wings that uses echolocation",
         "keywords":["cave","wings","fly","night","mammal","echolocation","animal"]},
        {"name":"Sports equipment", "definition":"a club used to hit a ball in games such as cricket or baseball",
         "keywords":["cricket","baseball","ball","hit","batter","match","sports","wood"]},
    ],
    "apple": [
        {"name":"Fruit", "definition":"a round edible fruit produced by an apple tree",
         "keywords":["fruit","eat","tree","juice","red","green","sweet","orchard"]},
        {"name":"Technology company", "definition":"a company known for computers, phones and electronic devices",
         "keywords":["iphone","mac","computer","phone","technology","device","ios","laptop"]},
    ],
    "mouse": [
        {"name":"Small animal", "definition":"a small rodent with a pointed snout and long tail",
         "keywords":["animal","cheese","rodent","tail","trap","house","cat"]},
        {"name":"Computer input device", "definition":"a handheld pointing device used to control a computer cursor",
         "keywords":["computer","click","cursor","screen","laptop","keyboard","button","usb"]},
    ],
    "light": [
        {"name":"Illumination", "definition":"the natural or artificial energy that makes things visible",
         "keywords":["bright","lamp","sun","dark","shine","room","bulb","see"]},
        {"name":"Not heavy", "definition":"having little weight or being easy to lift",
         "keywords":["weight","heavy","bag","carry","feather","load","lift"]},
    ],
    "spring": [
        {"name":"Season", "definition":"the season between winter and summer",
         "keywords":["flowers","winter","summer","weather","blossom","warm","season"]},
        {"name":"Coiled metal object", "definition":"a flexible coil that returns to its original shape",
         "keywords":["metal","coil","compress","mechanism","machine","pressure","elastic"]},
        {"name":"Water source", "definition":"a place where water flows naturally out of the ground",
         "keywords":["water","source","ground","fresh","stream","fountain"]},
    ],
    "right": [
        {"name":"Correct", "definition":"being true, accurate or free from error",
         "keywords":["correct","answer","true","wrong","fact","solution","exact"]},
        {"name":"Direction", "definition":"the direction opposite to left",
         "keywords":["turn","left","direction","street","side","road"]},
        {"name":"Entitlement", "definition":"a moral or legal entitlement or freedom",
         "keywords":["law","freedom","human","legal","vote","permission","equal"]},
    ],
    "crane": [
        {"name":"Bird", "definition":"a large long-legged bird with a long neck",
         "keywords":["bird","wings","fly","nest","wetland","feathers"]},
        {"name":"Lifting machine", "definition":"a tall machine used to lift and move heavy objects",
         "keywords":["construction","lift","building","heavy","machine","load","site"]},
    ],
    "palm": [
        {"name":"Part of the hand", "definition":"the inner surface of the hand between fingers and wrist",
         "keywords":["hand","finger","wrist","skin","hold","touch"]},
        {"name":"Palm tree", "definition":"a tropical tree with a tall trunk and large leaves",
         "keywords":["tree","tropical","leaves","coconut","beach","garden"]},
    ],
    "seal": [
        {"name":"Marine animal", "definition":"a fish-eating marine mammal with flippers",
         "keywords":["ocean","sea","animal","flippers","swim","water"]},
        {"name":"Official mark or closure", "definition":"a device or mark that closes or authenticates something",
         "keywords":["document","envelope","stamp","close","official","signature","package"]},
    ],
}

NEGATIONS = {"not","no","never","neither","nor","n't","cannot","can't","won't","don't","doesn't","didn't","isn't","aren't","wasn't","weren't","hardly","barely"}
REQUEST_WORDS = {"please","could","would","can","kindly","help","recommend","show","tell","give"}
QUESTION_START = {"what","why","when","where","who","whom","whose","which","how","is","are","am","do","does","did","can","could","would","will","should","have","has"}
COMMAND_VERBS = {"close","open","stop","start","explain","describe","show","tell","give","make","create","analyze","analyse","calculate","find","list","summarize","summarise","write","turn","bring","send"}
EMOTION_WORDS = {"happy","sad","excited","angry","afraid","love","hate","wonderful","terrible","amazing","awful","delighted","upset","worried","surprised"}

def clean_tokens(text: str) -> List[str]:
    return re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower())

@st.cache_resource(show_spinner=False)
def load_nlp():
    if spacy is None:
        return None, "spaCy is not installed. Install dependencies from requirements.txt."
    try:
        return spacy.load("en_core_web_sm"), None
    except Exception as exc:
        return None, f"English model unavailable: {exc}"

NLP, NLP_ERROR = load_nlp()

def parse_sentence(text: str):
    if NLP:
        return NLP(text)
    return None

def fallback_role_analysis(sentence: str) -> Dict:
    tokens = clean_tokens(sentence)
    if not tokens:
        return {"agent":"Not identified","action":"Not identified","theme":"Not identified","recipient":"Not identified","method":"Fallback rule-based parsing"}
    verbs = {"gave","give","sent","send","told","tell","explained","explain","showed","show","wrote","write","bought","buy","read","reads","ate","eat","kicked","kick","built","build","helped","help","opened","open","closed","close","chased","chase","made","make","found","find","called","call"}
    vi = next((i for i,w in enumerate(tokens) if w in verbs or w.endswith(("ed","ing"))), None)
    if vi is None:
        vi = 1 if len(tokens)>1 else 0
    agent = " ".join(tokens[:vi]) or "Not identified"
    action = tokens[vi] if vi < len(tokens) else "Not identified"
    rest = tokens[vi+1:]
    recipient = "Not identified"
    if "to" in rest:
        j = rest.index("to")
        theme = " ".join(rest[:j]) or "Not identified"
        recipient = " ".join(rest[j+1:]) or "Not identified"
    else:
        theme = " ".join(rest) or "Not identified"
    return {"agent":agent.title(),"action":action,"theme":theme.title(),"recipient":recipient.title(),"method":"Rule-based fallback"}

def role_analysis(sentence: str) -> Tuple[Dict, List[Dict]]:
    doc = parse_sentence(sentence)
    if doc is None:
        result = fallback_role_analysis(sentence)
        return result, [{"step":"Tokenization","detail":"Split the sentence into word tokens."},{"step":"Rule matching","detail":"Used a lightweight fallback pattern because the language model was unavailable."}]
    root = next((t for t in doc if t.dep_ == "ROOT"), None)
    if root is None:
        return fallback_role_analysis(sentence), []
    subjects = [t for t in root.children if t.dep_ in ("nsubj","nsubjpass","csubj")]
    objects = [t for t in root.children if t.dep_ in ("dobj","obj","attr","oprd","dative")]
    indirect = [t for t in root.children if t.dep_ in ("iobj",)]
    def phrase(token):
        subtree = sorted(token.subtree, key=lambda x:x.i)
        return " ".join(t.text for t in subtree)
    agent = phrase(subjects[0]) if subjects else "Not identified"
    theme = phrase(objects[0]) if objects else "Not identified"
    recipient = phrase(indirect[0]) if indirect else "Not identified"
    # A prepositional recipient such as "to the students"
    if recipient == "Not identified":
        for child in root.children:
            if child.dep_ == "prep" and child.lemma_.lower() in ("to","for"):
                pobj = next((c for c in child.children if c.dep_ == "pobj"), None)
                if pobj:
                    recipient = phrase(pobj)
                    break
    result = {"agent":agent,"action":root.lemma_,"theme":theme,"recipient":recipient,"method":"spaCy dependency parsing"}
    steps = [
        {"step":"Tokenization","detail":"spaCy split the sentence into tokens."},
        {"step":"Dependency parsing","detail":f"Identified '{root.text}' as the main predicate (ROOT)."},
        {"step":"Role mapping","detail":"Mapped subject, object and indirect-object dependencies to semantic role labels."},
    ]
    return result, steps

def wsd_analysis(sentence: str, target: str):
    target = target.lower().strip()
    tokens = set(clean_tokens(sentence))
    if target not in tokens:
        return None, f"'{target}' does not appear in the sentence."
    senses = SENSES.get(target)
    if not senses:
        return None, f"No built-in sense entries are available for '{target}'. Try one of: {', '.join(sorted(SENSES))}."
    context = tokens - {target}
    results = []
    for sense in senses:
        keywords = set(sense["keywords"])
        overlap = sorted(context & keywords)
        score = len(overlap)
        results.append({"Meaning":sense["name"],"Definition":sense["definition"],"Matching context words":", ".join(overlap) if overlap else "None","Score":score})
    results.sort(key=lambda x:x["Score"], reverse=True)
    # deterministic tie: if all zero, don't pretend certainty
    confident = results[0]["Score"] > 0 and (len(results)==1 or results[0]["Score"] > results[1]["Score"])
    selected = results[0] if results[0]["Score"] > 0 else None
    return {"context":sorted(context),"results":results,"selected":selected,"confident":confident,"target":target}, None

def negation_analysis(sentence: str):
    tokens = clean_tokens(sentence)
    found = [w for w in tokens if w in NEGATIONS]
    if not found:
        return {"negated":False,"markers":[],"scope":"No explicit negation marker detected.","interpretation":"The sentence is treated as affirmative by this rule-based detector."}
    scopes = []
    for marker in found:
        if marker in ("not","never","no","hardly","barely"):
            idx = tokens.index(marker)
            affected = tokens[idx+1:idx+5]
            scopes.append(" ".join(affected) if affected else "following clause")
        else:
            scopes.append("associated verb or phrase")
    return {"negated":True,"markers":found,"scope":"; ".join(scopes),"interpretation":"A negative expression was detected. The exact scope can depend on sentence structure and context."}

def intent_analysis(sentence: str):
    s = sentence.strip()
    words = clean_tokens(s)
    if not words:
        return {"intent":"Unknown","reason":"Enter a sentence to analyse."}
    lower = s.lower()
    polite_request = (
        "please" in words[:6]
        or (len(words) > 1 and words[0] in {"could", "would", "can"} and words[1] == "you")
        or (len(words) > 1 and words[0] == "kindly")
    )
    if polite_request:
        intent, reason = "Request", "Polite request cues such as 'please', 'could you' or 'would you' were detected."
    elif "?" in s or words[0] in QUESTION_START:
        intent, reason = "Question / Information seeking", "Question punctuation or an interrogative opening pattern was detected."
    elif words[0] in COMMAND_VERBS:
        intent, reason = "Command / Instruction", "The sentence begins with a verb commonly used to give instructions."
    elif any(w in EMOTION_WORDS for w in words) or "!" in s:
        intent, reason = "Emotional expression", "Emotion vocabulary or exclamation punctuation was detected."
    else:
        intent, reason = "Statement / Information", "No stronger question, request, command or emotion pattern was detected."
    return {"intent":intent,"reason":reason}

def graph_figure(roles: Dict):
    labels = [("Agent",roles["agent"]),("Action",roles["action"]),("Theme",roles["theme"]),("Recipient",roles["recipient"])]
    nodes = [(name,val) for name,val in labels if val and val != "Not identified"]
    if len(nodes) < 2:
        nodes = [("Sentence", "Input sentence"),("Action", roles.get("action","Not identified"))]
    # Arrange around a simple semantic spine
    xmap = {"Agent":0,"Action":1,"Theme":2,"Recipient":1}
    ymap = {"Agent":0,"Action":0,"Theme":0,"Recipient":-1}
    xs = [xmap.get(n,i) for i,(n,_) in enumerate(nodes)]
    ys = [ymap.get(n,0) for n,_ in nodes]
    edge_x, edge_y = [], []
    action_idx = next((i for i,(n,_) in enumerate(nodes) if n=="Action"), 0)
    for i in range(len(nodes)):
        if i != action_idx:
            edge_x += [xs[i],xs[action_idx],None]
            edge_y += [ys[i],ys[action_idx],None]
    edge_trace = go.Scatter(x=edge_x,y=edge_y,mode="lines",line=dict(width=2,color="#9eafa4"),hoverinfo="none")
    colors = {"Agent":"#dce9e1","Action":"#e9e2f0","Theme":"#e1ebf1","Recipient":"#f3e5da","Sentence":"#e9e2f0"}
    node_trace = go.Scatter(
        x=xs,y=ys,mode="markers+text",
        marker=dict(size=58,color=[colors.get(n,"#e9e2f0") for n,_ in nodes],line=dict(width=1,color="#c8d3ca")),
        text=[f"<b>{n}</b><br>{v[:28]}" for n,v in nodes],
        textposition="bottom center",textfont=dict(size=11,color="#33443f"),
        hovertext=[f"{n}: {v}" for n,v in nodes],hoverinfo="text"
    )
    fig=go.Figure([edge_trace,node_trace])
    fig.update_layout(height=360,margin=dict(l=20,r=20,t=20,b=65),showlegend=False,
        xaxis=dict(visible=False),yaxis=dict(visible=False),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
    return fig

def export_payload(module: str, sentence: str, result):
    return {"application":"SEMANTIX","module":module,"input":sentence,"result":result}

# ----------------------------- Reusable UI -----------------------------
def page_header(kicker, title, subtitle):
    st.markdown(f'<div class="eyebrow">{kicker}</div><h1>{title}</h1><p class="soft">{subtitle}</p>', unsafe_allow_html=True)
    st.write("")

def download_json(module, sentence, result, key):
    payload = export_payload(module, sentence, result)
    st.download_button("↓  Download analysis as JSON", json.dumps(payload, indent=2, ensure_ascii=False),
                       file_name=f"semantix_{module.lower().replace(' ','_')}.json",
                       mime="application/json", key=key)

def show_steps(steps):
    with st.expander("How did the system process this?", expanded=True):
        for i, step in enumerate(steps,1):
            st.markdown(f"**{i}. {step['step']}**")
            st.caption(step["detail"])

# ----------------------------- Sidebar -----------------------------
with st.sidebar:
    st.markdown("## ✳ semantix.")
    st.caption("SEMANTIC INTERPRETATION LAB")
    st.divider()
    page = st.radio("WORKSPACE", [
        "Overview","Semantic Role Analyzer","Word Sense Disambiguation",
        "Negation Analyzer","Intent Detector","Semantic Relationship Map"
    ], label_visibility="visible")
    st.divider()
    st.markdown("**Analysis engine**")
    if NLP:
        st.success("English parser loaded")
        st.caption("spaCy · en_core_web_sm")
    else:
        st.warning("Fallback mode active")
        st.caption("Role analysis uses lightweight rules. Other modules remain available.")
    st.divider()
    st.caption("A learning-focused NLP project. Results are explainable and may not cover every linguistic construction.")

# ----------------------------- Overview -----------------------------
if page == "Overview":
    st.markdown("""
    <div class="hero">
      <div class="eyebrow">Natural Language Processing · Project Workspace</div>
      <h1>Understanding language,<br>one meaning at a time.</h1>
      <p>SEMANTIX explores how words and sentences communicate meaning. Select a module to analyse semantic roles, ambiguous words, negation, speaker intent and relationships.</p>
    </div>
    """, unsafe_allow_html=True)
    st.subheader("Explore the workspace")
    cards = [
        ("01","Semantic Role Analyzer","Identify who performs an action and what is affected.","#dce9e1"),
        ("02","Word Sense Disambiguation","Choose the contextually suitable meaning of an ambiguous word.","#e9e2f0"),
        ("03","Negation Analyzer","Detect negative expressions and inspect their local scope.","#e1ebf1"),
        ("04","Intent Detector","Classify the communicative purpose of a sentence.","#f3e5da"),
        ("05","Semantic Relationship Map","Visualize links between sentence roles.","#e8e8dc"),
    ]
    cols=st.columns(2)
    for i,(num,title,desc,color) in enumerate(cards):
        with cols[i%2]:
            st.markdown(f'<div class="module-card" style="background:{color}"><div class="eyebrow">{num} / MODULE</div><h3>{title}</h3><p>{desc}</p></div>',unsafe_allow_html=True)
            st.write("")
    st.markdown('<div class="note">Tip: Start with the sample sentences inside each module. Then try your own sentence and inspect the processing explanation.</div>',unsafe_allow_html=True)
    st.subheader("Try a sample sentence")
    sample=st.selectbox("Choose an example",[
        "The teacher explained the lesson to the students.",
        "I deposited money in the bank.",
        "The children did not finish their homework.",
        "Could you please open the window?",
        "The girl gave her friend a book."
    ])
    st.code(sample,language=None)
    st.caption("Choose a module from the sidebar to analyse this type of sentence.")

# ----------------------------- Semantic roles -----------------------------
elif page == "Semantic Role Analyzer":
    page_header("MODULE 01 · PREDICATE–ARGUMENT STRUCTURE","Semantic Role Analyzer","Break a sentence into the participant roles that help express its meaning.")
    sentence=st.text_area("Enter a sentence", "The teacher explained the lesson to the students.", height=100, key="role_input")
    if st.button("Analyse semantic roles", type="primary", key="role_btn"):
        if not sentence.strip():
            st.error("Please enter a sentence first.")
        else:
            result,steps=role_analysis(sentence)
            st.session_state["role_result"]=(sentence,result,steps)
    if "role_result" in st.session_state:
        old_sentence,result,steps=st.session_state["role_result"]
        if old_sentence == sentence:
            st.markdown("### Interpretation")
            cols=st.columns(4)
            for col,(label,key,color) in zip(cols,[("AGENT","agent","#dce9e1"),("ACTION","action","#e9e2f0"),("THEME","theme","#e1ebf1"),("RECIPIENT","recipient","#f3e5da")]):
                with col:
                    st.markdown(f'<div class="kpi" style="background:{color}"><div class="kpi-label">{label}</div><div class="kpi-value" style="font-size:17px">{result[key]}</div></div>',unsafe_allow_html=True)
            st.write("")
            st.markdown('<div class="note">The predicate is the central action or state. Its arguments identify the participants and entities connected to it.</div>',unsafe_allow_html=True)
            show_steps(steps)
            download_json("Semantic Role Analysis",sentence,result,"role_json")
            with st.expander("Show token-level dependency information"):
                doc=parse_sentence(sentence)
                if doc:
                    data=[{"Token":t.text,"Lemma":t.lemma_,"Part of speech":t.pos_,"Dependency":t.dep_,"Head":t.head.text} for t in doc]
                    st.dataframe(pd.DataFrame(data),use_container_width=True,hide_index=True)
                else:
                    st.info("Token-level dependency details require the spaCy English model.")

# ----------------------------- WSD -----------------------------
elif page == "Word Sense Disambiguation":
    page_header("MODULE 02 · LEXICAL SEMANTICS","Word Sense Disambiguation","Discover which meaning of an ambiguous word best fits its surrounding context.")
    sentence=st.text_area("Enter a sentence", "I deposited money in the bank.", height=90, key="wsd_sentence")
    present=clean_tokens(sentence)
    candidates=sorted(set(present) & set(SENSES.keys()))
    default_target=candidates[0] if candidates else "bank"
    target=st.selectbox("Choose the ambiguous word",sorted(set(candidates+list(SENSES.keys()))),index=sorted(set(candidates+list(SENSES.keys()))).index(default_target))
    st.caption("Built-in demonstration lexicon: "+", ".join(sorted(SENSES.keys())))
    if st.button("Interpret word meaning",type="primary",key="wsd_btn"):
        result,error=wsd_analysis(sentence,target)
        if error: st.error(error)
        else: st.session_state["wsd_result"]=(sentence,target,result)
    if "wsd_result" in st.session_state:
        old_s,old_t,result=st.session_state["wsd_result"]
        if old_s==sentence and old_t==target:
            st.markdown("### Candidate meaning comparison")
            st.dataframe(pd.DataFrame(result["results"]),use_container_width=True,hide_index=True)
            if result["selected"]:
                st.success(f"Most suitable meaning: {result['selected']['Meaning']}")
                st.write(result["selected"]["Definition"])
                if not result["confident"]:
                    st.warning("The top score is tied. The application shows the leading candidate, but the context does not provide a unique answer.")
            else:
                st.warning("No matching context keywords were found. The system cannot confidently choose a meaning.")
            st.markdown("**Context words detected:** "+(", ".join(result["context"]) or "None"))
            show_steps([
                {"step":"Context extraction","detail":"The sentence was tokenized and the target word was removed from the context set."},
                {"step":"Sense comparison","detail":"Context words were compared with the curated keywords associated with each candidate meaning."},
                {"step":"Overlap scoring","detail":"Each shared keyword adds one point. The highest score is selected; ties are reported as uncertain."},
            ])
            download_json("Word Sense Disambiguation",sentence,result,"wsd_json")
    with st.expander("How does the Simplified Lesk approach work?"):
        st.latex(r"\operatorname{Score}(sense)=|Context(sentence)\cap Keywords(sense)|")
        st.caption("This educational implementation uses a small curated sense inventory and keyword overlap. It is a simplified Lesk-style method, not a full dictionary-based Lesk implementation.")

# ----------------------------- Negation -----------------------------
elif page == "Negation Analyzer":
    page_header("MODULE 03 · COMPOSITIONAL MEANING","Negation Analyzer","Explore how words such as 'not', 'never' and 'no' change the meaning of a sentence.")
    sentence=st.text_area("Enter a sentence","The students did not complete the assignment.",height=90,key="neg_sentence")
    if st.button("Analyse negation",type="primary",key="neg_btn"):
        if not sentence.strip(): st.error("Please enter a sentence.")
        else: st.session_state["neg_result"]=(sentence,negation_analysis(sentence))
    if "neg_result" in st.session_state:
        old_s,result=st.session_state["neg_result"]
        if old_s==sentence:
            c1,c2=st.columns(2)
            with c1:
                st.markdown('<div class="kpi"><div class="kpi-label">NEGATION DETECTED</div><div class="kpi-value">'+("Yes" if result["negated"] else "No")+'</div></div>',unsafe_allow_html=True)
            with c2:
                st.markdown('<div class="kpi"><div class="kpi-label">MARKERS FOUND</div><div class="kpi-value">'+(", ".join(result["markers"]) if result["markers"] else "None")+'</div></div>',unsafe_allow_html=True)
            st.write("")
            st.markdown("**Possible scope**")
            st.info(result["scope"])
            st.markdown("**Interpretation**")
            st.write(result["interpretation"])
            show_steps([
                {"step":"Tokenization","detail":"The sentence was converted into lowercase word tokens."},
                {"step":"Negation lookup","detail":"Tokens were checked against a list of common negative markers."},
                {"step":"Scope heuristic","detail":"For common markers, a short following-word window is displayed as a possible scope. This is an approximation, not a complete syntactic scope parser."},
            ])
            download_json("Negation Analysis",sentence,result,"neg_json")
    with st.expander("Try these examples"):
        st.write("- I like this book.")
        st.write("- I do not like this book.")
        st.write("- Nobody attended the meeting.")
        st.write("- She never misses class.")

# ----------------------------- Intent -----------------------------
elif page == "Intent Detector":
    page_header("MODULE 04 · PRAGMATICS","Intent Detector","Estimate the communicative purpose behind a sentence using transparent linguistic cues.")
    sentence=st.text_area("Enter a sentence","Could you please explain semantic interpretation?",height=90,key="intent_sentence")
    if st.button("Detect intent",type="primary",key="intent_btn"):
        if not sentence.strip(): st.error("Please enter a sentence.")
        else: st.session_state["intent_result"]=(sentence,intent_analysis(sentence))
    if "intent_result" in st.session_state:
        old_s,result=st.session_state["intent_result"]
        if old_s==sentence:
            st.markdown("### Detected communication type")
            st.markdown(f'<div class="hero"><div class="eyebrow">PREDICTED INTENT</div><h1 style="font-size:30px">{result["intent"]}</h1><p>{result["reason"]}</p></div>',unsafe_allow_html=True)
            st.markdown("**Decision cues**")
            st.write("The classifier checks punctuation, opening words, polite request expressions, common imperative verbs and emotion vocabulary in a fixed priority order.")
            show_steps([
                {"step":"Text normalization","detail":"The sentence is converted to lowercase tokens while retaining punctuation for question and exclamation checks."},
                {"step":"Cue matching","detail":"The rule-based classifier checks interrogative, request, command and emotion patterns."},
                {"step":"Intent assignment","detail":"The first matching category in the decision order is returned."},
            ])
            download_json("Intent Detection",sentence,result,"intent_json")
    with st.expander("Try different intent categories"):
        st.write("- What time is the lecture?")
        st.write("- Please send me the notes.")
        st.write("- Close the door.")
        st.write("- I am delighted with the result.")

# ----------------------------- Relationship map -----------------------------
elif page == "Semantic Relationship Map":
    page_header("MODULE 05 · MEANING REPRESENTATION","Semantic Relationship Map","Turn a sentence into a visual representation of its participants and their relationships.")
    sentence=st.text_area("Enter a sentence","The girl gave her friend a book.",height=90,key="graph_sentence")
    if st.button("Generate meaning map",type="primary",key="graph_btn"):
        if not sentence.strip(): st.error("Please enter a sentence.")
        else:
            roles,steps=role_analysis(sentence)
            st.session_state["graph_result"]=(sentence,roles,steps)
    if "graph_result" in st.session_state:
        old_s,roles,steps=st.session_state["graph_result"]
        if old_s==sentence:
            st.plotly_chart(graph_figure(roles),use_container_width=True,config={"displayModeBar":False})
            st.markdown("### Relationship table")
            rows=[
                {"From":roles["agent"],"Relationship":"performs","To":roles["action"]},
                {"From":roles["action"],"Relationship":"acts on","To":roles["theme"]},
                {"From":roles["action"],"Relationship":"directed to","To":roles["recipient"]},
            ]
            rows=[r for r in rows if r["From"]!="Not identified" and r["To"]!="Not identified"]
            st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
            show_steps(steps+[{"step":"Graph construction","detail":"The extracted roles become nodes; labeled connections represent their relationships to the predicate."}])
            download_json("Semantic Relationship Map",sentence,roles,"graph_json")

st.divider()
st.markdown('<div style="text-align:center;color:#849087;font-size:12px;padding:8px">SEMANTIX · Natural Language Processing Project · Semantic Interpretation</div>',unsafe_allow_html=True)
