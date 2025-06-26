import {ProductList} from "./components/ProductList";

function App() {
    return (
        <main className="min-h-screen bg-slate-900 p-4 sm:p-8">
            <div className="mx-auto w-full max-w-7xl">
                <ProductList/>
            </div>
        </main>
    )
}

export default App