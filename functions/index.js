name: Deploy Firebase (Hosting + Functions)

on:
  push:
    branches: [ main ]
    paths:
      - "functions/**"
      - "public/**"
      - "firebase.json"
      - ".firebaserc"
      - ".github/workflows/firebase-functions-deploy.yml"

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install Firebase CLI
        run: npm i -g firebase-tools

      - name: Auth with Google
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.FIREBASE_SERVICE_ACCOUNT_LANGUAGE_ACADEMY_3E1DE }}

      - name: Install Functions deps
        run: |
          if [ -f functions/package-lock.json ]; then
            npm ci --prefix functions
          else
            npm install --prefix functions
          fi

      - name: Deploy Functions + Hosting
        run: firebase deploy --project language-academy-3e1de --only functions,hosting --non-interactive
