// src/components/CommentCard.tsx
import {ThumbsUp, MessageSquare, Edit, Trash2} from "lucide-react";
import {useState} from 'react';
import {useMutation, useQueryClient} from "@tanstack/react-query";
import apiClient from "../api";
import toast from "react-hot-toast";
import {useAuthStore} from "../stores/authStore";
import {AddCommentForm} from "./AddCommentForm";
import {useCheckOwnership} from "../hooks/useCheckOwnership";

export interface Comment {
    id: number;
    review: number;
    user: User;
    text: string;
    created: string;
    likes_count: number;
    is_liked: boolean;
    children?: Comment[];
}

interface UserProfile {
    avatar: string | null;
}

interface User {
    username: string;
    profile: UserProfile;
}

interface CommentCardProps {
    comment: Comment;
}

const toggleCommentLike = (commentId: number) => {
    return apiClient.post(`/comments/${commentId}/like/`);
};
const deleteComment = (commentId: number) => apiClient.delete(`/comments/delete/${commentId}/`);
const updateComment = ({id, text}: { id: number; text: string }) => apiClient.patch(`/comments/update/${id}/`, {text});

export function CommentCard({comment}: CommentCardProps) {
    const {isLoggedIn} = useAuthStore();
    const queryClient = useQueryClient();
    const isOwner = useCheckOwnership(comment.user?.username);

    const [isReplying, setIsReplying] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [editText, setEditText] = useState(comment.text);

    const avatarUrl = comment.user.profile?.avatar
        ? `${import.meta.env.VITE_API_BASE_URL}${comment.user.profile.avatar}`
        : `https://ui-avatars.com/api/?name=${comment.user.username}&background=random&size=96`;

    const mutation = useMutation({
        mutationFn: toggleCommentLike,
        onSuccess: () => {
            queryClient.invalidateQueries({queryKey: ['comments', comment.review]});
        },
        onError: () => toast.error('Не удалось оценить комментарий.'),
    });

    const handleLike = () => {
        if (!isLoggedIn) {
            toast.error('Войдите, чтобы оценить комментарий.');
            return;
        }
        mutation.mutate(comment.id);
    };

    const likeMutation = useMutation({
        mutationFn: toggleCommentLike,
        onSuccess: () => {
            queryClient.invalidateQueries({queryKey: ['comments', comment.review]});
        },
        onError: () => toast.error('Не удалось оценить комментарий.'),
    });

    const deleteMutation = useMutation({
        mutationFn: deleteComment,
        onSuccess: () => {
            toast.success('Комментарий удален');
            queryClient.invalidateQueries({queryKey: ['comments', comment.review]});
        },
        onError: () => toast.error('Не удалось удалить комментарий.'),
    });

    const updateMutation = useMutation({
        mutationFn: updateComment,
        onSuccess: () => {
            toast.success('Комментарий обновлен');
            setIsEditing(false);
            queryClient.invalidateQueries({queryKey: ['comments', comment.review]});
        },
        onError: () => toast.error('Не удалось обновить комментарий.'),
    });

    const handleDelete = () => {
        if (window.confirm('Вы уверены, что хотите удалить этот комментарий?')) {
            deleteMutation.mutate(comment.id);
        }
    };

    const handleUpdate = (e: React.FormEvent) => {
        e.preventDefault();
        if (editText.trim() && editText.trim() !== comment.text) {
            updateMutation.mutate({id: comment.id, text: editText.trim()});
        } else {
            setIsEditing(false);
            setEditText(comment.text);
        }
    };

    return (
        <div className="flex items-start gap-3">
            <img src={avatarUrl} alt={comment.user.username}
                 className="h-8 w-8 rounded-full bg-slate-700 object-cover"/>

            <div className="flex-grow">
                <div className="rounded-md bg-slate-700/50 px-3 py-2">
                    <div className="flex items-center justify-between">
                        <span className="text-sm font-semibold text-white">{comment.user.username}</span>
                        <span className="text-xs text-slate-500">{new Date(comment.created).toLocaleDateString()}</span>
                    </div>
                    {isEditing ? (
                        <form onSubmit={handleUpdate} className="mt-2 space-y-2">
                            <textarea value={editText} onChange={(e) => setEditText(e.target.value)}
                                      className="w-full rounded-md border-slate-600 bg-slate-900/50 p-2 text-sm text-white"
                                      rows={2}/>
                            <div className="flex gap-2">
                                <button type="submit" disabled={updateMutation.isPending}
                                        className="rounded bg-cyan-600 px-2 py-1 text-xs text-white hover:bg-cyan-700">Сохранить
                                </button>
                                <button type="button" onClick={() => {
                                    setIsEditing(false);
                                    setEditText(comment.text);
                                }}
                                        className="rounded bg-slate-600 px-2 py-1 text-xs text-white hover:bg-slate-500">Отмена
                                </button>
                            </div>
                        </form>
                    ) : (
                        <p className="mt-1 text-sm text-slate-300">{comment.text}</p>
                    )}
                </div>
                {!isEditing && (
                    <div className="mt-1 flex items-center gap-4 pl-1">
                        <button
                            onClick={handleLike}
                            disabled={likeMutation.isPending}
                            className={`flex items-center gap-1.5 text-xs transition disabled:opacity-50 ${
                                    comment.is_liked ? 'text-cyan-400' : 'text-slate-400 hover:text-cyan-400'
                                }`}
                        >
                            <ThumbsUp size={14}
                                      className={comment.is_liked ? 'fill-cyan-400/20 stroke-cyan-400' : ''}/>
                            <span>{comment.likes_count}</span>
                        </button>
                        <button onClick={() => setIsReplying(!isReplying)}
                                className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-cyan-400">
                            <MessageSquare size={14}/>
                            <span>Ответить</span>
                        </button>
                        {isOwner && (
                            <>
                                <button onClick={() => setIsEditing(true)}
                                        className="text-xs text-slate-400 hover:text-cyan-400"><Edit size={14}/>
                                </button>
                                <button onClick={handleDelete} disabled={deleteMutation.isPending}
                                        className="text-xs text-slate-400 hover:text-red-500"><Trash2 size={14}/>
                                </button>
                            </>
                        )}
                    </div>
                )}
                {isReplying && (
                    <div className="mt-2">
                        <AddCommentForm reviewId={comment.review} parentId={comment.id}
                                        onSuccess={() => setIsReplying(false)}/>
                    </div>
                )}
            </div>
        </div>
    );
}