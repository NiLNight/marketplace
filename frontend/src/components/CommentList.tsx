// src/components/CommentList.tsx
import {useQuery} from '@tanstack/react-query';
import {useState} from 'react';
import apiClient from '../api';
import {CommentCard, type Comment} from './CommentCard';
import {ChevronDown} from 'lucide-react';

const fetchComments = async (reviewId: number): Promise<Comment[]> => {
    const {data} = await apiClient.get(`/comments/${reviewId}/`);
    return data.results || [];
};

/**
 * Компонент для отображения ОДНОГО комментария и его дочерних элементов (ответов).
 * У него своя, независимая логика для сворачивания/разворачивания ответов.
 */
function CommentNode({comment}: { comment: Comment }) {
    // Состояние видимости ответов для ЭТОГО конкретного комментария
    const [areRepliesVisible, setAreRepliesVisible] = useState(false);

    const children = comment.children || [];

    // Показываем ответы, если нажали "Показать еще"
    const visibleReplies = areRepliesVisible
        ? children
        // Или показываем только один самый популярный ответ, если он проходит порог
        : children.length > 0 && children[0].likes_count > comment.likes_count / 2
            ? [children[0]]
            : [];

    // Считаем, сколько ответов скрыто
    const hiddenRepliesCount = children.length - visibleReplies.length;

    return (
        <div key={comment.id}>
            <CommentCard comment={comment}/>

            {/* Рекурсивно рендерим видимые ответы */}
            {visibleReplies.length > 0 && (
                <div className="ml-4 mt-3 space-y-3 border-l-2 border-slate-700 pl-4">
                    {visibleReplies.map(reply => (
                        // Каждый дочерний элемент - это тоже CommentNode со своей логикой
                        <CommentNode key={reply.id} comment={reply}/>
                    ))}
                </div>
            )}

            {/* Кнопка "Показать еще" для ответов */}
            {hiddenRepliesCount > 0 && !areRepliesVisible && (
                <div className="ml-8 mt-2">
                    <button
                        onClick={() => setAreRepliesVisible(true)}
                        className="flex items-center gap-2 text-xs text-cyan-400 hover:underline"
                    >
                        <ChevronDown size={14}/>
                        Показать еще {hiddenRepliesCount} ответа(ов)
                    </button>
                </div>
            )}
        </div>
    );
}

/**
 * Главный компонент, который загружает и отображает комментарии ВЕРХНЕГО УРОВНЯ.
 */
export function CommentList({reviewId}: { reviewId: number }) {
    const {data: comments, isLoading} = useQuery({
        queryKey: ['comments', reviewId],
        queryFn: () => fetchComments(reviewId),
    });

    if (isLoading) return <div className="text-sm text-slate-400 mt-2">Загрузка комментариев...</div>;

    const rootComments = comments || [];

    return (
        <div className="space-y-4">
            {rootComments.map(comment => (
                <CommentNode key={comment.id} comment={comment}/>
            ))}
        </div>
    );
}