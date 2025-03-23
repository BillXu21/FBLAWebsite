from flask import Blueprint, request, jsonify, session, render_template
from sqlalchemy.sql import text
from database_manager import db
from datetime import datetime

messages_bp = Blueprint('messages', __name__, url_prefix='/messages')

# Route to fetch conversations
@messages_bp.route('/conversations', methods=['GET'])
def get_conversations():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session['user_id']

    conversations = db.session.execute(
        text(
            """
            SELECT shared_id, participant1_id, participant2_id,
                   MAX(CASE WHEN participant1_id = :user_id THEN u2.email ELSE u1.email END) AS other_user_email,
                   MAX(c.notifications) AS unread_count
            FROM conversations c
            JOIN user u1 ON c.participant1_id = u1.id
            JOIN user u2 ON c.participant2_id = u2.id
            WHERE c.participant1_id = :user_id OR c.participant2_id = :user_id
            GROUP BY shared_id
            """
        ),
        {"user_id": user_id}
    ).fetchall()

    return jsonify([
        {
            "id": convo.shared_id,
            "participant1_id": convo.participant1_id,
            "participant2_id": convo.participant2_id,
            "other_user_email": convo.other_user_email,
            "unread_count": convo.unread_count
        } for convo in conversations
    ])

# Route to start a conversation
@messages_bp.route('/start_conversation', methods=['POST'])
def start_conversation():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session['user_id']
    data = request.json
    other_user_email = data.get('email')

    other_user = db.session.execute(
        text("SELECT id FROM user WHERE email = :email"),
        {"email": other_user_email}
    ).fetchone()

    if not other_user:
        return jsonify({"error": "User not found"}), 404

    other_user_id = other_user.id

    # Check if conversation already exists
    conversation = db.session.execute(
        text(
            """
            SELECT shared_id FROM conversations
            WHERE (participant1_id = :user_id AND participant2_id = :other_user_id)
               OR (participant1_id = :other_user_id AND participant2_id = :user_id)
            """
        ),
        {"user_id": user_id, "other_user_id": other_user_id}
    ).fetchone()

    if conversation:
        return jsonify({"conversation_id": conversation.shared_id}), 200

    # Create a new conversation
    shared_id = str(user_id) + "_" + str(other_user_id)
    db.session.execute(
        text(
            """
            INSERT INTO conversations (shared_id, participant1_id, participant2_id, notifications)
            VALUES (:shared_id, :user_id, :other_user_id, 0), (:shared_id, :other_user_id, :user_id, 0)
            """
        ),
        {"shared_id": shared_id, "user_id": user_id, "other_user_id": other_user_id}
    )
    db.session.commit()

    return jsonify({"conversation_id": shared_id}), 201

# Endpoint to fetch messages in a conversation
@messages_bp.route('/<shared_id>', methods=['GET'])
def get_messages(shared_id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session['user_id']

    # Reset the unread notifications count for the current user
    db.session.execute(
        text(
            """
            UPDATE conversations
            SET notifications = 0
            WHERE shared_id = :shared_id AND participant1_id = :user_id
            """
        ),
        {"shared_id": shared_id, "user_id": user_id}
    )
    db.session.commit()

    messages = db.session.execute(
        text(
            """
            SELECT m.id, m.sender_id, m.recipient_id, m.content, m.timestamp, u.email as sender_email
            FROM messages m
            JOIN user u ON m.sender_id = u.id
            WHERE m.conversation_id = :shared_id
            ORDER BY m.timestamp
            """
        ),
        {"shared_id": shared_id}
    ).fetchall()

    return jsonify([
        {
            "id": msg.id,
            "sender_id": msg.sender_id,
            "recipient_id": msg.recipient_id,
            "content": msg.content,
            "timestamp": datetime.strptime(msg.timestamp, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
            if isinstance(msg.timestamp, str) else msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "sender_email": msg.sender_email
        } for msg in messages
    ])

# Endpoint to send a message
@messages_bp.route('/send', methods=['POST'])
def send_message():
    print('lollol')
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session['user_id']
    data = request.json

    shared_id = data.get('conversation_id')
    content = data.get('content')

    if not content:
        return jsonify({"error": "Message content cannot be empty"}), 400

    # Get the other participant in the conversation
    conversation = db.session.execute(
        text(
            """
            SELECT participant1_id, participant2_id
            FROM conversations
            WHERE shared_id = :shared_id
            """
        ),
        {"shared_id": shared_id}
    ).fetchone()

    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404

    recipient_id = (
        conversation.participant2_id
        if conversation.participant1_id == user_id
        else conversation.participant1_id
    )

    # Insert the message into the database
    db.session.execute(
        text(
            """
            INSERT INTO messages (conversation_id, sender_id, recipient_id, content, timestamp)
            VALUES (:shared_id, :sender_id, :recipient_id, :content, CURRENT_TIMESTAMP)
            """
        ),
        {
            "shared_id": shared_id,
            "sender_id": user_id,
            "recipient_id": recipient_id,
            "content": content,
        },
    )

    # Increment the notifications count for the recipient
    db.session.execute(
        text(
            """
            UPDATE conversations
            SET notifications = notifications + 1
            WHERE participant1_id = :recipient_id AND participant2_id = :sender_id
            """
        ),
        {"recipient_id": recipient_id, "sender_id": user_id}
    )

    db.session.commit()
    return jsonify({"success": True}), 201

# Render the chat window
@messages_bp.route('/chat/<shared_id>', methods=['GET'])
def chat_window(shared_id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    return render_template('chat.html', conversation_id=shared_id)

# Render the messages home page
@messages_bp.route('/', methods=['GET'])
def messages_home():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    return render_template('messages.html')
