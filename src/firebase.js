// /src/firebase.js
import firebase from "firebase/app";
import "firebase/messaging";

const firebaseConfig = {
  apiKey: "AIzaSyDUIdVPKOCDsmOuoet6NofXoJzleiXMtHw",  // Your API Key
  authDomain: "language-academy-3e1de.firebaseapp.com",  // Your Auth Domain
  projectId: "language-academy-3e1de",  // Your Project ID
  storageBucket: "language-academy-3e1de.appspot.com",  // Your Storage Bucket
  messagingSenderId: "849327205750",  // Your Messaging Sender ID
  appId: "1:849327205750:web:2de0e6ed20c55d4f8d9e57",  // Your App ID
  measurementId: "YOUR_MEASUREMENT_ID",  // Your Measurement ID (optional)
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Retrieve Firebase messaging instance
const messaging = firebase.messaging();

// Request permission to send notifications
export const requestPermission = async () => {
  try {
    await Notification.requestPermission();
    console.log("Notification permission granted.");
    const token = await messaging.getToken({ vapidKey: "YOUR_VAPID_KEY" }); // Optional VAPID key for web push
    console.log("FCM Token:", token);
    // Save this token to your database to send notifications later
  } catch (error) {
    console.error("Permission denied", error);
  }
};

// Handle incoming messages
messaging.onMessage((payload) => {
  console.log("Message received:", payload);
  // You can display the notification here
  new Notification(payload.notification.title, {
    body: payload.notification.body,
    icon: payload.notification.icon,
  });
});

export default messaging;
