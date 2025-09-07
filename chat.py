import streamlit as st
from openai import OpenAI
from groq import Groq
import requests

# Streamlit app title
st.title("3-Agent LLM Discussion with Contextual Memory: GPT-3.5, LLAMA-3 & GPT-4o")

# Privacy and usage notice
st.info(
    "🔒 **Privacy Notice:** Enter your API keys below. "
    "Keys are only used for this session, are not saved, stored, or logged, and are only sent to the APIs for processing your requests."
)

# Exciting topic suggestions
suggested_topics = [
    "AI's Impact on Creative Industries",
    "Ethics of Autonomous Vehicles",
    "Future of Quantum Computing",
    "Space Colonization: Mars vs. Moon",
    "Cryptocurrency Regulation Challenges",
    "Rise of Generative AI in Education",
    "Deepfake Technology: Threat or Tool?",
    "Impact of Social Media on Mental Health",
    "Climate Change Solutions: Tech Innovations",
    "Virtual Reality: Future of Remote Work"
]

# Step 1: Enter the topic first
st.subheader("Step 1: Enter Discussion Topic")

if "topic" not in st.session_state:
    st.session_state.topic = ""

topic_input = st.text_input("Enter a topic for the agents to discuss:", value=st.session_state.topic)

if not topic_input:
    st.markdown("**TRY:** " + ", ".join([f"`{t}`" for t in suggested_topics]))

if not topic_input:
    selected_topic = st.selectbox("Or select from popular topics:", [""] + suggested_topics)
    if selected_topic:
        st.session_state.topic = selected_topic
        topic_input = selected_topic

if topic_input:
    st.session_state.topic = topic_input
    topic = topic_input
else:
    topic = None

if topic:
    st.success(f"Topic selected: {topic}. Now configure your settings.")

    # Step 2: Sidebar for API keys and settings
    st.sidebar.header("Step 2: Settings")
    st.sidebar.write(
        "Enter your API keys below. **Keys are used only in your current session and are never stored.**"
    )
    openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    groq_api_key = st.sidebar.text_input("Groq API Key", type="password")
    serpapi_key = st.sidebar.text_input("SerpAPI Key", type="password")
    turns = st.sidebar.slider("Number of Turns", min_value=1, max_value=10, value=3)

    # Editable model selection
    st.sidebar.markdown("---")
    st.sidebar.subheader("Model Selection (Editable)")
    alex_model = st.sidebar.text_input(
        "Alex (GPT-3.5) Model", value="gpt-3.5-turbo"
    )
    luna_model = st.sidebar.text_input(
        "Luna (LLaMA) Model", value="llama-3.3-70b-versatile"  # use up-to-date model by default!
    )
    gina_model = st.sidebar.text_input(
        "Gina (GPT-4o) Model", value="gpt-4o"
    )

    if openai_api_key and groq_api_key and serpapi_key:
        openai_client = OpenAI(api_key=openai_api_key)
        groq_client = Groq(api_key=groq_api_key)
    else:
        st.error("Please provide all three API keys in the sidebar.")
        st.stop()

    agents = [
        {"name": "Alex (GPT-3.5)", "client": openai_client, "model": alex_model},
        {"name": "Luna (LLaMA)", "client": groq_client, "model": luna_model},
        {"name": "Gina (GPT-4o)", "client": openai_client, "model": gina_model}
    ]

    def web_search(query):
        try:
            if not serpapi_key:
                return "Search failed: SerpAPI key not provided."
            url = "https://serpapi.com/search.json"
            params = {
                "engine": "google",
                "q": query,
                "api_key": serpapi_key
            }
            response = requests.get(url, params=params)
            data = response.json()
            if "organic_results" in data:
                results = data["organic_results"]
                search_summary = ""
                for result in results[:2]:
                    title = result.get("title", "No title")
                    link = result.get("link", "No link")
                    snippet = result.get("snippet", "No description")
                    search_summary += f"**[{title}]({link})**\n{snippet}\n\n"
                return search_summary or "No relevant search results found."
            else:
                return "No search results found."
        except Exception as e:
            return f"Search failed: {str(e)}"

    def get_response(agent, chat_history, topic):
        system_prompt = (
            f"You are {agent['name']}, an AI participating in a group discussion. "
            f"Your role is to actively engage in the conversation, build on previous arguments, ask questions, "
            f"and challenge or support other agents' points of view. "
            f"Maintain the context and keep the discussion cohesive. "
            f"Topic: '{topic}'. Chat history:\n\n{chat_history}\n\n"
            f"Respond concisely (2-3 sentences) and contribute to the flow of discussion. "
            f"You can also ask relevant questions to other agents or propose alternative perspectives. "
            f"To fetch web info, start your message with 'SEARCH: <query>' (e.g., 'SEARCH: Nvidia AI market share')."
        )
        try:
            response = agent["client"].chat.completions.create(
                model=agent["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "What do you think?"}
                ],
                max_tokens=150,
                temperature=0.7
            )
            text = response.choices[0].message.content.strip()
            if text.startswith("SEARCH:"):
                query = text.split("SEARCH:")[1].strip()
                search_result = web_search(query)
                return f"{agent['name']} searched '{query}': {search_result}\nThen said: {text[len('SEARCH: ' + query):].strip() or 'Interesting info!'}"
            return text
        except Exception as e:
            return f"Error: {str(e)}"

    st.subheader("Step 3: Start Discussion")
    if st.button("Start Discussion"):
        chat_history = f"Discussion Topic: {topic}\n\n"
        st.subheader("Discussion")
        st.write(f"**Topic**: {topic}")
        for turn in range(turns):
            with st.expander(f"Turn {turn + 1}", expanded=(turn == 0)):
                turn_history = ""
                for agent in agents:
                    with st.spinner(f"{agent['name']} is thinking..."):
                        response = get_response(agent, chat_history, topic)
                        turn_history += f"**{agent['name']}**: {response}\n\n"
                        chat_history += f"{agent['name']}: {response}\n"
                    st.markdown(f"**{agent['name']}**: {response}")
        st.success("Discussion concluded!")
