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
const app = initializeApp(firebaseConfig);

// Initialize Firebase Messaging
const messaging = getMessaging(app);

// Request permission and get token
async function requestPermissionAndGetToken() {
  try {
    await requestPermission();
    const token = await getToken(messaging);
    if (token) {
      console.log('FCM Token:', token);
      // Save this token to send notifications later
    } else {
      console.error('No token available.');
    }
  } catch (error) {
    console.error('Permission denied or error occurred:', error);
  }
}

requestPermissionAndGetToken();

export { messaging };
