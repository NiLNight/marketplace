// src/components/ReviewCard.tsx
import {ThumbsUp, MessageSquare, Edit} from 'lucide-react';
import {useAuthStore} from '../stores/authStore';
import apiClient from '../api';
import toast from 'react-hot-toast';
import {useQueryClient, useMutation} from '@tanstack/react-query';
import {useState} from 'react';
import {CommentList} from './CommentList';
import {AddCommentForm} from './AddCommentForm';
import {useCheckOwnership} from '../hooks/useCheckOwnership';
import {EditReviewForm} from './EditReviewForm';

export interface Review {
    id: number;
    user: User;
    value: number;
    text: string;
    image: string | null;
    created: string;
    likes_count: number;
    comments_count: number;
    is_liked: boolean;
}

interface UserProfile {
    avatar: string | null;
}

interface User {
    username: string;
    profile: UserProfile;
}

interface ReviewCardProps {
    review: Review;
    productId: number;
}

const toggleLike = (reviewId: number) => apiClient.post(`/reviews/${reviewId}/like/`);

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
    const [isEditing, setIsEditing] = useState(false);
    const isOwner = useCheckOwnership(review.user?.username);
    const baseUrl = import.meta.env.VITE_API_BASE_URL;

    const avatarUrl = review.user.profile?.avatar
        ? review.user.profile.avatar.startsWith('http') ? review.user.profile.avatar : `${baseUrl}${review.user.profile.avatar}`
        : `https://ui-avatars.com/api/?name=${review.user.username}&background=random`;

    const imageUrl = review.image
        ? review.image.startsWith('http') ? review.image : `${baseUrl}${review.image}`
        : null;

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
            {isEditing ? (
                <EditReviewForm review={review} productId={productId} onCancel={() => setIsEditing(false)}/>
            ) : (
                <div className="flex items-start gap-4">
                    <img src={avatarUrl} alt={review.user.username}
                         className="h-10 w-10 rounded-full bg-slate-700 object-cover"/>

                    <div className="flex-grow">
                        <div className="flex items-center justify-between">
                            <span className="font-semibold text-white">{review.user.username}</span>
                            <span
                                className="text-xs text-slate-500">{new Date(review.created).toLocaleDateString()}</span>
                        </div>
                        <div className="flex items-center gap-1 text-yellow-400 mt-1">
                            {Array.from({length: 5}).map((_, i) => (
                                <span key={i}
                                      className={i < review.value ? 'text-yellow-400' : 'text-slate-600'}>★</span>
                            ))}
                        </div>
                        {review.text && <p className="mt-3 text-slate-300">{review.text}</p>}
                        {imageUrl && (
                            <img src={imageUrl} alt="Изображение к отзыву"
                                 className="mt-3 max-h-64 w-auto rounded-lg"/>
                        )}
                        <div className="mt-4 flex items-center gap-4 border-t border-slate-700/50 pt-3">
                            <button
                                onClick={handleLikeClick}
                                disabled={mutation.isPending}
                                className={`flex items-center gap-2 text-sm transition disabled:opacity-50 ${
                                    review.is_liked
                                        ? 'text-cyan-400'
                                        : 'text-slate-400 hover:text-cyan-400'
                                }`}>
                                <ThumbsUp
                                    size={16}
                                    className={review.is_liked ? 'fill-cyan-400/20 stroke-cyan-400' : ''}
                                />
                                <span>{review.likes_count}</span>
                            </button>
                            <button onClick={() => setShowComments(!showComments)}
                                    className="flex items-center gap-2 text-sm text-slate-400 transition hover:text-cyan-400">
                                <MessageSquare size={16}/>
                                <span>{review.comments_count > 0 ? `${review.comments_count} ${getCommentDeclension(review.comments_count)}` : 'Комментировать'}</span>
                            </button>
                            {isOwner && (
                                <button onClick={() => setIsEditing(true)}
                                        className="flex items-center gap-2 text-sm text-slate-400 transition hover:text-cyan-400">
                                    <Edit size={16}/>
                                    <span>Редактировать</span>
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            )}
            {showComments && (
                <div className="mt-4 pl-11">
                    <div className="border-t border-slate-700/50 pt-4 space-y-4">
                        {isLoggedIn && (<AddCommentForm reviewId={review.id} onSuccess={() => {
                        }}/>)}
                        <CommentList reviewId={review.id}/>
                    </div>
                </div>
            )}
        </div>
    );
}