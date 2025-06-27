// src/hooks/useLockedBody.ts
import {useLayoutEffect} from 'react';

// Финальная, самая надежная версия хука для блокировки прокрутки.
// Он не вычисляет ширину скроллбара, а использует position: fixed,
// что решает все проблемы со сдвигами и конфликтами с DevTools.
export function useLockedBody(isLocked: boolean): void {
    useLayoutEffect(() => {
        if (!isLocked) {
            return;
        }

        // Сохраняем исходные стили и позицию скролла
        const originalBodyStyle = document.body.style.cssText;
        const scrollY = window.scrollY;

        // Применяем стили для блокировки
        document.body.style.position = 'fixed';
        document.body.style.top = `-${scrollY}px`;
        document.body.style.width = '100%';
        document.body.style.overflowY = 'scroll'; // Важно, чтобы избежать "прыжка" при исчезновении скроллбара

        // Функция для очистки, которая вернет все как было
        return () => {
            document.body.style.cssText = originalBodyStyle;
            window.scrollTo(0, scrollY);
        };
    }, [isLocked]);
}