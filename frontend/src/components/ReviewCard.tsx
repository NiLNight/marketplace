// src/components/ReviewCard.tsx
import {ThumbsUp, UserCircle2, MessageSquare} from 'lucide-react';
import {useAuthStore} from '../stores/authStore';
import apiClient from '../api';
import toast from 'react-hot-toast';
import {useQueryClient, useMutation} from '@tanstack/react-query';
import {useState} from 'react';
import {CommentList} from './CommentList';
import {AddCommentForm} from './AddCommentForm';

export interface Review {
    id: number;
    user: string;
    value: number;
    text: string;
    image: string | null;
    created: string;
    likes_count: number;
    comments_count: number;
}

interface ReviewCardProps {
    review: Review;
    productId: number;
}

const toggleLike = (reviewId: number) => {
    return apiClient.post(`/reviews/${reviewId}/like/`);
};

// Вспомогательная функция для правильного склонения
function getCommentDeclension(count: number): string {
    const cases = [2, 0, 1, 1, 1, 2];
    const titles = ['комментарий', 'комментария', 'комментариев'];
    const index = (count % 100 > 4 && count % 100 < 20) ? 2 : cases[(count % 10 < 5) ? count % 10 : 5];
    return titles[index];
}


export function ReviewCard({review, productId}: ReviewCardProps) {
    const {isLoggedIn} = useAuthStore();
    const queryClient = useQueryClient();
    const [showComments, setShowComments] = useState(false);

    const mutation = useMutation({
        mutationFn: toggleLike,
        onSuccess: () => {
            queryClient.invalidateQueries({queryKey: ['reviews', productId]});
        },
        onError: () => toast.error('Не удалось поставить лайк.'),
    });

    const handleLikeClick = () => {
        if (!isLoggedIn) {
            toast.error('Пожалуйста, войдите, чтобы оценить отзыв.');
            return;
        }
        mutation.mutate(review.id);
    };

    return (
        <div className="rounded-lg bg-slate-800 p-4">
            <div className="flex items-start gap-4">
                <UserCircle2 size={32} className="mt-1 text-slate-400 flex-shrink-0"/>
                <div className="flex-grow">
                    <div className="flex items-center justify-between">
                        <span className="font-semibold text-white">{review.user}</span>
                        <span className="text-xs text-slate-500">{new Date(review.created).toLocaleDateString()}</span>
                    </div>
                    <div className="flex items-center gap-1 text-yellow-400 mt-1">
                        {Array.from({length: 5}).map((_, i) => (
                            <span key={i} className={i < review.value ? 'text-yellow-400' : 'text-slate-600'}>★</span>
                        ))}
                    </div>
                    {review.text && <p className="mt-3 text-slate-300">{review.text}</p>}
                    {review.image && (
                        <img
                            src={`${import.meta.env.VITE_API_BASE_URL}${review.image}`}
                            alt="Изображение к отзыву"
                            className="mt-3 max-h-64 w-auto rounded-lg"
                        />
                    )}

                    <div className="mt-4 flex items-center gap-4 border-t border-slate-700/50 pt-3">
                        <button onClick={handleLikeClick} disabled={mutation.isPending}
                                className="flex items-center gap-2 text-sm text-slate-400 transition hover:text-cyan-400 disabled:opacity-50">
                            <ThumbsUp size={16}/>
                            <span>{review.likes_count}</span>
                        </button>
                        <button
                            onClick={() => setShowComments(!showComments)}
                            className="flex items-center gap-2 text-sm text-slate-400 transition hover:text-cyan-400"
                        >
                            <MessageSquare size={16}/>
                            <span>
                                {review.comments_count > 0
                                    ? `${review.comments_count} ${getCommentDeclension(review.comments_count)}`
                                    : 'Комментировать'
                                }
                            </span>
                        </button>
                    </div>
                </div>
            </div>

            {showComments && (
                <div className="mt-4 pl-11">
                    <div className="border-t border-slate-700/50 pt-4 space-y-4">
                        {isLoggedIn && (
                            <AddCommentForm
                                reviewId={review.id}
                                onSuccess={() => { /* Форма сама сбрасывается, доп. действия не нужны */
                                }}
                            />
                        )}
                        <CommentList reviewId={review.id} reviewLikes={review.likes_count} showAll={showComments} />
                    </div>
                </div>
            )}
        </div>
    );
}