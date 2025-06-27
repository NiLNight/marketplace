// src/App.tsx
import {Outlet} from 'react-router-dom';
import {Header} from "./components/Header";
import {Footer} from "./components/Footer"; // <-- Импортируем Footer

function App() {
    return (
        <div className="flex flex-col min-h-screen bg-slate-900">
            <Header/>
            <main className="flex-grow p-4 sm:p-8">
                <Outlet/>
            </main>
            <Footer/> {/* <-- Добавляем Footer */}
        </div>
    );
}

export default App;