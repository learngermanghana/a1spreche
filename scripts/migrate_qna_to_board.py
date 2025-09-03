"""Migration script to move class_qna questions to class_board posts."""

import firebase_admin
from firebase_admin import firestore


def migrate():
    firebase_admin.initialize_app()
    db = firestore.client()
    qna_ref = db.collection("class_qna")
    batch = db.batch()
    ops = 0
    for class_doc in qna_ref.stream():
        class_name = class_doc.id
        questions_ref = class_doc.reference.collection("questions")
        for qdoc in questions_ref.stream():
            qdata = qdoc.to_dict() or {}
            post_data = {
                "content": qdata.get("question"),
                "posted_by_name": qdata.get("asked_by_name"),
                "posted_by_code": qdata.get("asked_by_code"),
                "created_at": qdata.get("timestamp"),
                "topic": qdata.get("topic", ""),
            }
            if qdata.get("updated_at") is not None:
                post_data["updated_at"] = qdata.get("updated_at")

            post_ref = (
                db.collection("class_board")
                .document(class_name)
                .collection("posts")
                .document(qdoc.id)
            )
            batch.set(post_ref, post_data)
            ops += 1

            replies_ref = qdoc.reference.collection("replies")
            for rdoc in replies_ref.stream():
                rdata = rdoc.to_dict() or {}
                comment_data = {
                    "content": rdata.get("reply_text"),
                    "commented_by_name": rdata.get("replied_by_name"),
                    "commented_by_code": rdata.get("replied_by_code"),
                    "created_at": rdata.get("timestamp"),
                }
                if rdata.get("updated_at") is not None:
                    comment_data["updated_at"] = rdata.get("updated_at")

                comment_ref = post_ref.collection("comments").document(rdoc.id)
                batch.set(comment_ref, comment_data)
                ops += 1

                if ops >= 450:
                    batch.commit()
                    batch = db.batch()
                    ops = 0

        if ops:
            batch.commit()
            batch = db.batch()
            ops = 0


if __name__ == "__main__":
    migrate()
