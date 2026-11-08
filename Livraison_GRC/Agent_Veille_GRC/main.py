from agent.collector import collect_all, display_articles
from agent.processor import process_articles
from agent.ai_analyzer import analyze_articles
from agent.database import save_articles


def main():
    print("\n================================")
    print("       AGENT DE VEILLE GRC")
    print("================================")

    articles = collect_all()
    processed_articles = process_articles(articles)
    analyzed_articles = analyze_articles(processed_articles)

    save_articles(analyzed_articles)
    display_articles(analyzed_articles)

    print("\n================================")
    print("       TRAITEMENT TERMINE")
    print("================================")


if __name__ == "__main__":
    main()