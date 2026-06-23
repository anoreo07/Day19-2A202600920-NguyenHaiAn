import os
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from fastembed import TextEmbedding
from feast import FeatureStore

class HybridMemoryAgent:
    def __init__(self, qdrant_path: str = ":memory:", feast_repo_path: str = "app/feast_repo") -> None:
        # 1. Initialize embedder
        self.embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        
        # 2. Initialize Qdrant Client (in-memory by default)
        self.client = QdrantClient(qdrant_path)
        self.collection_name = "bonus_memory"
        
        # Recreate or ensure collection exists
        existing = {c.name for c in self.client.get_collections().collections}
        if self.collection_name not in existing:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
        
        # 3. Initialize Feast Feature Store
        # Resolve absolute path relative to project root
        self.project_root = Path(__file__).resolve().parent.parent
        self.feast_store = FeatureStore(repo_path=str(self.project_root / feast_repo_path))
        self.point_counter = 0

    def remember(self, text: str, user_id: str = "u_001") -> None:
        """Add a new piece of episodic memory for this user in Qdrant vector store."""
        vector = next(self.embedder.embed([text])).tolist()
        
        point = PointStruct(
            id=self.point_counter,
            vector=vector,
            payload={
                "user_id": user_id,
                "text": text
            }
        )
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        self.point_counter += 1

    def recall(self, query: str, user_id: str = "u_001") -> str:
        """Retrieve top-K memories from Qdrant + user profile features from Feast -> return assembled context."""
        # 1. Vector lookup from Qdrant
        q_vec = next(self.embedder.embed([query])).tolist()
        
        # Filter to isolate memories per user_id
        user_filter = Filter(
            must=[
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=user_id)
                )
            ]
        )
        
        hits = self.client.query_points(
            collection_name=self.collection_name,
            query=q_vec,
            query_filter=user_filter,
            limit=3
        ).points
        
        memories = [h.payload["text"] for h in hits]

        # 2. Stable profile features from Feast Feature Store
        REQUEST_FEATURES = [
            "user_profile_features:reading_speed_wpm",
            "user_profile_features:preferred_language",
            "user_profile_features:topic_affinity",
            "query_velocity_features:queries_last_hour",
            "query_velocity_features:distinct_topics_24h",
        ]
        
        feast_res = self.feast_store.get_online_features(
            features=REQUEST_FEATURES,
            entity_rows=[{"user_id": user_id}],
        ).to_dict()
        
        # Extract features (since to_dict returns lists)
        reading_speed = feast_res.get("reading_speed_wpm", [None])[0]
        preferred_lang = feast_res.get("preferred_language", [None])[0]
        topic_affinity = feast_res.get("topic_affinity", [None])[0]
        queries_last_hour = feast_res.get("queries_last_hour", [None])[0]
        distinct_topics_24h = feast_res.get("distinct_topics_24h", [None])[0]

        # 3. Assemble final context
        context_parts = []
        context_parts.append("=== USER PROFILE FEATURES (Feast) ===")
        context_parts.append(f"User ID: {user_id}")
        context_parts.append(f"Preferred Language: {preferred_lang}")
        context_parts.append(f"Reading Speed (WPM): {reading_speed}")
        context_parts.append(f"Topic Affinity: {topic_affinity}")
        context_parts.append(f"Queries Last Hour: {queries_last_hour}")
        context_parts.append(f"Distinct Topics Last 24 Hours: {distinct_topics_24h}")
        context_parts.append("")
        
        context_parts.append("=== RELEVANT EPISODIC MEMORIES (Qdrant) ===")
        if memories:
            for i, mem in enumerate(memories, 1):
                context_parts.append(f"  {i}. {mem}")
        else:
            context_parts.append("  (No relevant memories found.)")
        context_parts.append("")
        
        context_parts.append("=== SYSTEM PROMPT / INSTRUCTIONS ===")
        # Dynamic customization based on profile features
        lang_instruction = "Respond in Vietnamese." if preferred_lang == "vi" else "Respond in English."
        speed_instruction = "Keep responses concise." if (reading_speed and reading_speed > 250) else "Provide detailed step-by-step explanations."
        fatigue_instruction = "Note: User has made many requests recently. Suggest taking a break if appropriate." if (queries_last_hour and queries_last_hour > 10) else ""
        
        context_parts.append(f"- {lang_instruction}")
        context_parts.append(f"- Tailor response topics to user affinity: {topic_affinity}.")
        context_parts.append(f"- {speed_instruction}")
        if fatigue_instruction:
            context_parts.append(f"- {fatigue_instruction}")

        return "\n".join(context_parts)
