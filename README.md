## A trading platform


## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.


## Starting the backend:
First:
```bash
cd src/app/backen # given you are in the hyjacked directory
# then
uvicorn main:app --reload # If you encounter errors it may be the way uvicorn needs to be invoked

# e.g.

python3 uvicorn main:app --reload
```

## Database:


## This will be Deployed onto Vercel and other hosting services

## NEW:

Now fully enabled for docker, using doppler CLI, you will now be able to fork this project where ever without worry, as long as you use doppler CLI

## Usage:

``` bash
doppler run -- docker compose up --build
```