import gradio as gr
import asyncio
import logging
from system.main import LLMDebateSystem
from system.config import Config, ModelConfig
from system.dynamic_config import create_small_model_config_only

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gradio_app")

debate_system = None

async def initialize_system():
    global debate_system
    if debate_system is not None:
        return
    result = await create_small_model_config_only()
    if not result or result[0] is None:
        raise Exception("No suitable small models found")
    orchestrator_config, debater_configs = result
    if hasattr(orchestrator_config, 'model'):
        orchestrator_model = orchestrator_config.model
    else:
        orchestrator_model = str(orchestrator_config)
    if debater_configs and hasattr(debater_configs[0], 'model'):
        debater_models = [config.model for config in debater_configs]
    else:
        debater_models = [str(config) for config in debater_configs]
    Config.ORCHESTRATOR_MODEL = ModelConfig(
        name="Orchestrator",
        model=orchestrator_model,
        temperature=0.3,
        max_tokens=2000,
        personality="analytical and diplomatic",
        system_prompt="""You are an expert debate orchestrator. Your role is to:\n1. Analyze responses from three debater LLMs\n2. Determine if they have reached consensus\n3. Provide feedback to help them converge\n4. Synthesize final summaries when consensus is reached\nBe objective, thorough, and focus on finding common ground."""
    )
    debater_personalities = [
        ("Analytical_Debater", "analytical and fact-focused", "You are an analytical debater who focuses on facts, data, and logical reasoning."),
        ("Creative_Debater", "creative and perspective-oriented", "You are a creative debater who brings unique perspectives and innovative thinking."),
        ("Pragmatic_Debater", "pragmatic and solution-oriented", "You are a pragmatic debater focused on practical solutions and real-world applications.")
    ]
    Config.DEBATER_MODELS = []
    for i, (name, personality, system_prompt) in enumerate(debater_personalities):
        if i < len(debater_models):
            Config.DEBATER_MODELS.append(ModelConfig(
                name=name,
                model=debater_models[i],
                temperature=0.6 + (i * 0.1),
                max_tokens=800,
                personality=personality,
                system_prompt=system_prompt
            ))
    debate_system = LLMDebateSystem()
    await debate_system.initialize()

async def debate_async(question, max_rounds):
    await initialize_system()
    result = await debate_system.conduct_debate(question=question, max_rounds=max_rounds)
    summary = result.final_summary or "No summary available"
    rounds = result.rounds
    round_outputs = []
    for r in rounds:
        round_text = f"Round {r.round_number}:\n"
        for resp in r.debater_responses:
            round_text += f"- {getattr(resp, 'debater_name', 'Debater')}: {resp.response}\n"
        if r.orchestrator_feedback:
            round_text += f"Orchestrator: {r.orchestrator_feedback}\n"
        round_outputs.append(round_text)
    consensus = result.consensus_reached
    return summary, "\n\n".join(round_outputs), f"Consensus reached: {consensus}", f"Total rounds: {result.total_rounds}"

def debate_interface(question, max_rounds):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    summary, rounds, consensus, total_rounds = loop.run_until_complete(debate_async(question, max_rounds))
    return summary, rounds, consensus, total_rounds

desc = """
# LLM Debate System (Gradio UI)

- Enter your debate question below.
- The system will run a 3-agent debate and show the summary, all rounds, and consensus.
- Share the public Gradio link for remote access (appears after launch).
"""

with gr.Blocks() as demo:
    gr.Markdown(desc)
    with gr.Row():
        question = gr.Textbox(label="Debate Question", placeholder="Enter your debate topic/question here", lines=2)
        max_rounds = gr.Number(label="Max Rounds", value=3, precision=0)
    run_btn = gr.Button("Start Debate")
    with gr.Row():
        summary = gr.Textbox(label="Final Summary", lines=3)
    with gr.Row():
        rounds = gr.Textbox(label="All Rounds", lines=10)
    with gr.Row():
        consensus = gr.Textbox(label="Consensus", lines=1)
        total_rounds = gr.Textbox(label="Total Rounds", lines=1)
    run_btn.click(debate_interface, inputs=[question, max_rounds], outputs=[summary, rounds, consensus, total_rounds])

demo.launch(share=True)
