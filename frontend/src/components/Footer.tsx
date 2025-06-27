// src/components/Footer.tsx
export function Footer() {
    const currentYear = new Date().getFullYear();
    return (
        <footer className="mt-auto bg-slate-800 text-slate-400 text-center p-4">
            <p>© {currentYear} Marketplace. Все права защищены.</p>
        </footer>
    );
}