// App.tsx

import { Outlet } from 'react-router-dom';
import { Header} from "./components/Header.tsx";

function App() {
  return (
    // Это наш общий Layout для всех страниц
    <main className="min-h-screen bg-slate-900 p-4 sm:p-8">
      <Header />  {/* 2. Добавляем компонент Header сюда. Он будет над всеми страницами */}

      {/* <Outlet /> — это место, куда React Router будет "вставлять"
          нужный компонент страницы (`ProductCatalogPage` или `ProductDetailPage`)
          в зависимости от текущего URL. */}
      <Outlet />

      {/* <Footer /> <-- здесь мог бы быть общий футер */}
    </main>
  );
}

export default App;