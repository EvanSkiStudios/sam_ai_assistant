import faiss
import numpy as np
import os
import json
import ollama


embedding_model = "nomic-embed-text"
# "snowflake-arctic-embed2"


def faiss_index_delete(user_name):
    # todo - called from message memory manager remove_user_conversation_file
    # will remove faiss database
    return None


def build_or_load_faiss_index(user_name):
    json_file_name = str(user_name) + '.json'

    running_dir = os.path.dirname(os.path.realpath(__file__))
    users_dir = os.path.join(running_dir, 'users')
    user_folder = os.path.join(users_dir, user_name)
    os.makedirs(user_folder, exist_ok=True)

    user_history_json = os.path.join(user_folder, json_file_name)
    if not os.path.exists(user_history_json):
        print(f"❌❌❌ FAISS ERROR> {json_file_name} is missing or does not exist, Aborting...")
        return None

    index_path = os.path.join(user_folder, user_name + "faiss_index.bin")
    metadata_path = os.path.join(user_folder, user_name + "metadata.json")
    embeddings_path = os.path.join(user_folder, user_name + "embeddings.npy")

    # Load latest JSON messages
    with open(user_history_json, "r", encoding="utf-8") as f:
        raw_messages = json.load(f)

    # Pair messages
    paired_messages = []
    i = 0
    while i < len(raw_messages):
        msg = raw_messages[i]
        if msg["role"] == "user" and i + 1 < len(raw_messages) and raw_messages[i + 1]["role"] == "assistant":
            paired_messages.append({
                "user": {"role": msg["role"], "name": msg.get("name"), "content": msg["content"]},
                "assistant": {"role": raw_messages[i+1]["role"], "name": raw_messages[i+1].get("name"), "content": raw_messages[i+1]["content"]}
            })
            i += 2
        else:
            paired_messages.append({
                msg["role"]: {"role": msg["role"], "name": msg.get("name"), "content": msg["content"]}
            })
            i += 1

    # If no cache, build from scratch
    if not (os.path.exists(metadata_path) and os.path.exists(embeddings_path) and os.path.exists(index_path)):
        print("No cache found, building from scratch...")
        return _build_from_scratch(paired_messages, index_path, metadata_path, embeddings_path)

    # Load existing cache
    with open(metadata_path, "r", encoding="utf-8") as f:
        cached_metadata = json.load(f)
    cached_embeddings = np.load(embeddings_path)
    index = faiss.read_index(index_path)

    # Compare cached vs fresh
    if paired_messages == cached_metadata:
        print("No changes detected, using cache.")
        return {"index": index, "metadata": cached_metadata, "embeddings": cached_embeddings}

    # If the cached data is a *prefix* of the new data → append only
    if len(paired_messages) > len(cached_metadata) and paired_messages[:len(cached_metadata)] == cached_metadata:
        new_messages = paired_messages[len(cached_metadata):]
        print(f"Detected {len(new_messages)} new messages, appending to index...")

        texts_for_embedding = []
        for pair in new_messages:
            if "user" in pair and "assistant" in pair:
                text = f"USER: {pair['user']['content']} ASSISTANT: {pair['assistant']['content']}"
            elif "user" in pair:
                text = f"USER: {pair['user']['content']}"
            else:
                text = f"ASSISTANT: {pair['assistant']['content']}"
            texts_for_embedding.append(text)

        # Embed only new messages
        new_vectors = []
        for text in texts_for_embedding:
            resp = ollama.embed(model=embedding_model, input=text)
            new_vectors.append(resp["embeddings"][0])

        new_vectors = np.array(new_vectors, dtype="float32")
        index.add(new_vectors)

        # Update caches
        cached_metadata.extend(new_messages)
        updated_embeddings = np.vstack([cached_embeddings, new_vectors])

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(cached_metadata, f, ensure_ascii=False, indent=2)
        np.save(embeddings_path, updated_embeddings)
        faiss.write_index(index, index_path)

        print("Index Loaded:", index.ntotal, "vectors")
        return {"index": index, "metadata": cached_metadata, "embeddings": updated_embeddings}

    # Otherwise → changes/deletes detected, rebuild
    print("Changes or deletions detected, rebuilding index from scratch...")
    return _build_from_scratch(paired_messages, index_path, metadata_path, embeddings_path)


def _build_from_scratch(paired_messages, index_path, metadata_path, embeddings_path):
    texts_for_embedding = []
    for pair in paired_messages:
        if "user" in pair and "assistant" in pair:
            text = f"USER: {pair['user']['content']} ASSISTANT: {pair['assistant']['content']}"
        elif "user" in pair:
            text = f"USER: {pair['user']['content']}"
        else:
            text = f"ASSISTANT: {pair['assistant']['content']}"
        texts_for_embedding.append(text)

    embedding_vectors = []
    for text in texts_for_embedding:
        resp = ollama.embed(model=embedding_model, input=text)
        embedding_vectors.append(resp["embeddings"][0])

    embedding_vectors = np.array(embedding_vectors, dtype="float32")
    dim = embedding_vectors.shape[1]

    index = faiss.IndexFlatL2(dim)
    # noinspection PyArgumentList
    index.add(embedding_vectors)

    faiss.write_index(index, index_path)
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(paired_messages, f, ensure_ascii=False, indent=2)
    np.save(embeddings_path, embedding_vectors)

    print("Index built:", index.ntotal, "vectors")
    return {"index": index, "metadata": paired_messages, "embeddings": embedding_vectors}


def search_faiss_index(query, index, metadata, top_k=3, max_distance=2.0):
    # Embed the query
    resp = ollama.embed(
        model=embedding_model,
        input=query
    )

    # Extract the actual vector
    query_vector = resp["embeddings"][0]

    # Convert to numpy array for FAISS
    query_vector_array = np.array([query_vector], dtype="float32")

    # Cap top_k to the actual number of vectors in the index
    top_k = min(top_k, index.ntotal)

    # Search
    distances, indices = index.search(query_vector_array, top_k)

    # Return metadata results
    retrieved_messages = []
    # Loop through the retrieved indices and distances, keeping track of ranking order
    for rank, (idx, dist) in enumerate(zip(indices[0], distances[0])):
        # Skip results that exceed the maximum allowed distance (i.e., too dissimilar)
        if dist > max_distance:
            continue
        # Append a structured dictionary with the relevant metadata and ranking info
        retrieved_messages.append({
            "rank": rank + 1,  # Rank starts at 1, not 0
            "distance": float(dist),  # Convert distance to float for consistency
            "context": metadata[idx]
        })

    return retrieved_messages


def get_relevant_messages(query, index, metadata):
    query_text = query
    retrieved_matches = search_faiss_index(query_text, index, metadata, 4)

    # print(f"[{match['rank']}] [dist={match['distance']:.4f}] {match['context']} ")

    message_groups = []
    for match in retrieved_matches:
        # Extract messages as a list of dicts
        message_list = list(match["context"].values())
        # Append the pair/group as-is to relevant_memories
        message_groups.append(message_list)

        # Reverse the order of the message groups, not the dicts inside
    message_groups.reverse()

    # Flatten the list of lists into a single list of dicts
    flattened_messages = [msg for group in message_groups for msg in group]

    # Convert the whole flattened list to JSON once
    json_str = json.dumps(flattened_messages, ensure_ascii=False, indent=2)  # Python object → string
    parsed = json.loads(json_str)  # string → Python object
    return parsed


def Test_database():
    faiss_data = build_or_load_faiss_index('evanski_')

    query = "this is only a test"
    memories = get_relevant_messages(query, faiss_data["index"], faiss_data["metadata"])

    print(memories)


if __name__ == "__main__":
    Test_database()
