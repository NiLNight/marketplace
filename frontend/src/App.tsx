// App.tsx

import { Outlet } from 'react-router-dom';

function App() {
  return (
    // Это наш общий Layout для всех страниц
    <main className="min-h-screen bg-slate-900 p-4 sm:p-8">
      {/* <Header />  <-- здесь могла бы быть общая шапка сайта */}

      {/* <Outlet /> — это место, куда React Router будет "вставлять"
          нужный компонент страницы (`ProductCatalogPage` или `ProductDetailPage`)
          в зависимости от текущего URL. */}
      <Outlet />

      {/* <Footer /> <-- здесь мог бы быть общий футер */}
    </main>
  );
}

export default App;