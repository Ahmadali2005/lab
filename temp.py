# bioverse_multilang_final.py
from flask import Flask, request, render_template_string
from gtts import gTTS
import os
import time
from deep_translator import GoogleTranslator
import networkx as nx
import json

app = Flask(__name__)

# ---------------- Knowledge Graph ----------------
G = nx.Graph()
G.add_node("Experiment: Microgravity Bone Study", url="https://example.com/microgravity-study",
           summary="Study on bone cells in microgravity shows loss of density and structural changes.")
G.add_node("Organism: Human Cells", summary="Human cells used in microgravity experiments.")
G.add_edge("Experiment: Microgravity Bone Study", "Organism: Human Cells", label="INVOLVES")

def graph_to_json():
    data = {"nodes": [], "links": []}
    for n, attrs in G.nodes(data=True):
        node_data = {"id": n}
        if "url" in attrs:
            node_data["url"] = attrs["url"]
        node_data["summary"] = attrs.get("summary", "")
        data["nodes"].append(node_data)
    for u, v, attrs in G.edges(data=True):
        data["links"].append({"source": u, "target": v, "label": attrs.get('label', '')})
    return json.dumps(data)

# ---------------- Translation ----------------
def translate_text(text, target='en'):
    try:
        return GoogleTranslator(source='auto', target=target).translate(text)
    except:
        return text

# ---------------- Text-to-Speech ----------------
def text_to_speech(text, lang='en'):
    os.makedirs("static", exist_ok=True)
    timestamp = int(time.time()*1000)
    filename = f"static/response_{timestamp}.mp3"
    tts = gTTS(text=text, lang=lang)
    tts.save(filename)
    return filename

# ---------------- Update Knowledge Graph ----------------
def update_knowledge_graph(question_en):
    new_nodes = []
    highlighted = None
    summary_text = ""
    q = question_en.lower()
    if "bone" in q:
        node_name = "Bone Cells"
        node_summary = "Bone Cells affected in microgravity show density loss and structural changes."
        G.add_node(node_name, summary=node_summary)
        G.add_edge("Experiment: Microgravity Bone Study", node_name, label="INVOLVES")
        new_nodes.append(node_name)
        highlighted = "Experiment: Microgravity Bone Study"
        summary_text = G.nodes[highlighted]["summary"]
        return summary_text, new_nodes, highlighted
    elif "cell" in q:
        node_name = "New Cell Research"
        node_summary = "New Cell Research explores cellular responses in microgravity."
        G.add_node(node_name, summary=node_summary)
        G.add_edge("Experiment: Microgravity Bone Study", node_name, label="RELATED")
        new_nodes.append(node_name)
        highlighted = "Experiment: Microgravity Bone Study"
        summary_text = G.nodes[highlighted]["summary"]
        return summary_text, new_nodes, highlighted
    else:
        return "Sorry, I don't understand that yet.", new_nodes, None

# ---------------- Routes ----------------
@app.route('/', methods=['GET', 'POST'])
def home():
    answer = ""
    translated = ""
    audio_file = ""
    vr_color = "blue"
    vr_position_y = 1.25
    vr_animation = ""
    new_vr_nodes = []
    background_img = "/static/space_lab_360.jpg"
    lang = "en"
    highlightedNode = None

    if request.method == 'POST':
        user_question = request.form.get('question')
        lang = request.form.get('lang', 'en')

        # ترجمة السؤال للإنجليزية داخليًا
        question_en = translate_text(user_question, target='en')

        # تحديث الـ graph والملخص
        answer, new_vr_nodes, highlightedNode = update_knowledge_graph(question_en)

        # ترجمة الجواب للغة المطلوبة
        if lang != 'en':
            translated = translate_text(answer, target=lang)

        # توليد الصوت بنفس لغة المستخدم
        text_for_audio = translated if translated else answer
        audio_file = text_to_speech(text_for_audio, lang)

        # VR dynamic
        if "bone" in question_en.lower():
            vr_color = "red"
            vr_position_y = 1.5
            vr_animation = "property: position; to: 0 2 -3; dur: 2000; dir: alternate; loop: true"
        elif "cell" in question_en.lower():
            vr_color = "green"
            vr_position_y = 1.0
            vr_animation = "property: rotation; to: 0 360 0; dur: 3000; loop: true; easing: linear"

    graph_json = graph_to_json()

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
  <title>BioVerse MultiLang</title>
  <script src="https://aframe.io/releases/1.4.0/aframe.min.js"></script>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>#graph { width: 600px; height: 400px; border:1px solid #ccc; }</style>
</head>
<body>
  <h1>🌍 BioVerse Multi-Language Chatbot</h1>

  <form method="POST">
    <input type="text" name="question" placeholder="Ask about space biology in any language..." style="width:350px;">
    <select name="lang">
      <option value="en" {% if lang=='en' %}selected{% endif %}>English</option>
      <option value="ar" {% if lang=='ar' %}selected{% endif %}>العربية</option>
    </select>
    <button type="submit">Ask</button>
  </form>

  {% if answer %}
    <h3>Answer / Study Summary:</h3>
    <p>{{ answer }}</p>
    {% if translated %}
      <p><b>Translated:</b> {{ translated }}</p>
    {% endif %}

    <h3>🔊 Listen:</h3>
    <audio controls>
      <source src="{{ audio_file }}" type="audio/mpeg">
      Your browser does not support the audio element.
    </audio>
  {% endif %}

  <h2>Knowledge Graph (Interactive D3.js)</h2>
  <div id="graph"></div>

  <h2>Immersive VR Simulation</h2>
  <a-scene embedded style="width:600px; height:400px;">
    <a-sky src="{{ background_img }}"></a-sky>
    <a-sphere position="0 {{ vr_position_y }} -3" radius="1" color="{{ vr_color }}"
              animation="{{ vr_animation }}"></a-sphere>
    <a-plane rotation="-90 0 0" width="10" height="10" color="#222" shadow></a-plane>
    {% for node in new_vr_nodes %}
    <a-entity position="{{ loop.index*2-3 }} 1 -2">
      <a-text value="{{ node }}" color="yellow" align="center" scale="2 2 2"></a-text>
      <a-box depth="0.5" height="0.5" width="0.5" color="orange">
        <a-animation attribute="rotation" to="0 360 0" dur="4000" repeat="indefinite"></a-animation>
      </a-box>
    </a-entity>
    {% endfor %}
  </a-scene>

  <script>
  const graphData = {{ graph_json | safe }};
  const highlightedNode = "{{ highlightedNode }}";
  const width = 600, height = 400;
  const svg = d3.select("#graph").append("svg")
      .attr("width", width).attr("height", height);

  const simulation = d3.forceSimulation(graphData.nodes)
      .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-400))
      .force("center", d3.forceCenter(width/2, height/2));

  const link = svg.append("g").attr("stroke", "#999").attr("stroke-opacity", 0.6)
      .selectAll("line").data(graphData.links).join("line").attr("stroke-width", 2);

  const tooltip = d3.select("body").append("div")
      .style("position", "absolute").style("padding", "5px 10px")
      .style("background", "#fff").style("border", "1px solid #999")
      .style("border-radius", "4px").style("pointer-events", "none")
      .style("opacity", 0);

  const node = svg.append("g").attr("stroke", "#fff").attr("stroke-width", 1.5)
      .selectAll("circle").data(graphData.nodes).join("circle")
      .attr("r", 20)
      .attr("fill", d => d.id === highlightedNode ? "orange" : "lightblue")
      .call(d3.drag()
          .on("start", (event,d) => { if(!event.active) simulation.alphaTarget(0.3).restart(); d.fx=d.x; d.fy=d.y; })
          .on("drag", (event,d) => { d.fx=event.x; d.fy=event.y; })
          .on("end", (event,d) => { if(!event.active) simulation.alphaTarget(0); d.fx=null; d.fy=null; })
      )
      .on("mouseover", (event,d) => {
          tooltip.transition().duration(200).style("opacity", 0.9);
          tooltip.html(d.summary || d.id)
                 .style("left", (event.pageX+5) + "px")
                 .style("top", (event.pageY-28) + "px");
      })
      .on("mouseout", () => tooltip.transition().duration(500).style("opacity", 0))
      .on("click", (event,d) => {
          if(d.url) window.open(d.url, "_blank");
      });

  const label = svg.append("g").selectAll("text")
      .data(graphData.nodes).join("text")
      .text(d => d.id)
      .attr("font-size", "10px").attr("text-anchor", "middle");

  simulation.on("tick", () => {
      link.attr("x1", d => d.source.x)
          .attr("y1", d => d.source.y)
          .attr("x2", d => d.target.x)
          .attr("y2", d => d.target.y);
      node.attr("cx", d => d.x).attr("cy", d => d.y);
      label.attr("x", d => d.x).attr("y", d => d.y - 25);
  });
  </script>
</body>
</html>
""", answer=answer, translated=translated, audio_file=audio_file,
       vr_color=vr_color, vr_position_y=vr_position_y, vr_animation=vr_animation,
       graph_json=graph_json, new_vr_nodes=new_vr_nodes,
       lang=lang, highlightedNode=highlightedNode)

if __name__ == '__main__':
    os.makedirs("static", exist_ok=True)
    app.run(debug=True, port=int(os.environ.get('PORT',5002)), host='0.0.0.0', use_reloader=False)

