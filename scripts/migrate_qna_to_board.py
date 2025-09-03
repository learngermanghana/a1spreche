"""Migration script to move class_qna questions to class_board posts."""

import firebase_admin
from firebase_admin import firestore


def migrate():
    firebase_admin.initialize_app()
    db = firestore.client()
    qna_ref = db.collection("class_qna")
    for class_doc in qna_ref.stream():
        class_name = class_doc.id
        questions_ref = class_doc.reference.collection("questions")
        for qdoc in questions_ref.stream():
            qdata = qdoc.to_dict() or {}
            post_data = {
                "content": qdata.get("question"),
                "posted_by_name": qdata.get("asked_by_name"),
                "posted_by_code": qdata.get("asked_by_code"),
                "timestamp": qdata.get("timestamp"),
                "topic": qdata.get("topic", ""),
            }
            post_ref = db.collection("class_board").document(class_name).collection("posts").document(qdoc.id)
            post_ref.set(post_data)

            replies_ref = qdoc.reference.collection("replies")
            for rdoc in replies_ref.stream():
                rdata = rdoc.to_dict() or {}
                comment_data = {
                    "comment_text": rdata.get("reply_text"),
                    "commented_by_name": rdata.get("replied_by_name"),
                    "commented_by_code": rdata.get("replied_by_code"),
                    "timestamp": rdata.get("timestamp"),
                }
                post_ref.collection("comments").document(rdoc.id).set(comment_data)


if __name__ == "__main__":
    migrate()
