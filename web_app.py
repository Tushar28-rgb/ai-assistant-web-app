"""Flask web UI for the AI Assistant."""

from flask import Flask, render_template, request, jsonify

from ai_assistant import (
    FUNCTIONS,
    get_feedback_stats,
    get_improvement_tips,
    is_demo_mode,
    run_with_prompt,
    save_feedback,
)

app = Flask(__name__)


@app.route("/")
def index():
    stats = get_feedback_stats()
    return render_template("index.html", functions=FUNCTIONS, stats=stats)


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True) or {}
    func_key = data.get("function", "")
    prompt_key = data.get("prompt_style", "")
    user_input = (data.get("user_input") or "").strip()

    if func_key not in FUNCTIONS:
        return jsonify({"error": "Invalid function selected."}), 400
    if not user_input:
        return jsonify({"error": "Please enter some text."}), 400

    func_cfg = FUNCTIONS[func_key]
    prompts = func_cfg["prompts"]
    if prompt_key not in prompts:
        return jsonify({"error": "Invalid prompt style selected."}), 400

    prompt_config = prompts[prompt_key]
    try:
        result = run_with_prompt(user_input, prompt_config)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Server error: {e}"}), 500

    return jsonify({
        "response": result,
        "category": func_cfg["label"],
        "prompt_name": prompt_config["name"],
        "query": user_input,
    })


@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json(silent=True) or {}
    category = data.get("category", "")
    query = data.get("query", "")
    prompt_name = data.get("prompt_name", "")
    helpful = data.get("helpful", "")
    comment = (data.get("comment") or "").strip()

    if helpful not in ("yes", "no"):
        return jsonify({"error": "Feedback must be 'yes' or 'no'."}), 400

    save_feedback(category, query, prompt_name, helpful, comment)
    tips = get_improvement_tips(category) if helpful == "no" else []
    stats = get_feedback_stats()

    return jsonify({"tips": tips, "stats": stats})


if __name__ == "__main__":
    print("\n  AI Assistant Web UI")
    if is_demo_mode():
        print("  DEMO MODE — sample responses, no API needed")
    else:
        print("  Tip: set $env:DEMO_MODE=\"1\" if API quota is exceeded")
    print("  Open in your browser: http://127.0.0.1:5000\n")
    app.run(debug=True, port=5000, use_reloader=False)
