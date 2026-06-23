import sys
from agent import HybridMemoryAgent

def main():
    print("Initializing HybridMemoryAgent POC...")
    agent = HybridMemoryAgent(qdrant_path=":memory:", feast_repo_path="app/feast_repo")

    # Seed the agent with episodic memory chunks for user "u_001"
    print("Seeding episodic memory in Qdrant...")
    memories = [
        "Kubernetes is an open-source system for automating deployment, scaling, and management of containerized applications.",
        "We set up VPC peering and private subnets in GCP to isolate the staging and production databases.",
        "To secure our cloud databases, we enforce TLS encryption on the wire and encryption at rest with AES-256.",
        "Auto-scaling configuration in AWS: scale CPU capacity up dynamically when traffic exceeds 80% utilization.",
        "Using zero-trust architecture helps protect our microservices by validating tokens at every single gateway endpoint."
    ]
    for mem in memories:
        agent.remember(mem, user_id="u_001")

    # Define the 5 demo queries
    queries = [
        ("1. Simple Lookup (Vector only)", "What have I read about Kubernetes?"),
        ("2. Profile-needed (Uses topic_affinity)", "Recommend what to read next"),
        ("3. Fresh-activity (Uses queries_last_hour)", "What am I focused on lately?"),
        ("4. Paraphrase (Vector wins)", "Documents about scaling infrastructure?"),
        ("5. Mixed (Hybrid + Profile)", "Give me a cloud security summary")
    ]

    print("\n" + "="*80)
    print("RUNNING DEMO QUERIES")
    print("="*80 + "\n")

    for title, query in queries:
        print(f"--- Query Title: {title} ---")
        print(f"Query text: {query!r}")
        print("-" * 50)
        context = agent.recall(query, user_id="u_001")
        print(context)
        print("\n" + "="*80 + "\n")

    print("Demo completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
