(() => {
    const firebaseConfig = {
        apiKey: "AIzaSyDs7jNX-eO67NrrsMmnykOU77GWel7GFZs",
        authDomain: "pali-exam-builder-250ac.firebaseapp.com",
        projectId: "pali-exam-builder-250ac",
        storageBucket: "pali-exam-builder-250ac.firebasestorage.app",
        messagingSenderId: "250371814811",
        appId: "1:250371814811:web:ce01d919ed656fbe889d3e",
        measurementId: "G-4M2MB4JSYT"
    };
    try {
        if (typeof firebase === 'undefined' || !firebase.initializeApp) return;
        if (firebase.apps && firebase.apps.length) return;
        firebase.initializeApp(firebaseConfig);
    } catch (_) {}
})();
