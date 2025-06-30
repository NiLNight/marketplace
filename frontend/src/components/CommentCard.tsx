// src/components/CommentCard.tsx
import {ThumbsUp, UserCircle2, MessageSquare} from "lucide-react";
import {useState} from 'react';
import {useMutation, useQueryClient} from "@tanstack/react-query";
import apiClient from "../api";
import toast from "react-hot-toast";
import {useAuthStore} from "../stores/authStore";
import {AddCommentForm} from "./AddCommentForm";

export interface Comment {
    id: number;
    review: number;
    user: string;
    text: string;
    created: string;
    likes_count: number;
    children?: Comment[];
}

interface CommentCardProps {
    comment: Comment;
}

const toggleCommentLike = (commentId: number) => {
    return apiClient.post(`/comments/${commentId}/like/`);
};

export function CommentCard({comment}: CommentCardProps) {
    const {isLoggedIn} = useAuthStore();
    const queryClient = useQueryClient();
    const [isReplying, setIsReplying] = useState(false);

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

    return (
        <div className="flex items-start gap-3">
            <UserCircle2 size={28} className="mt-1 text-slate-500 flex-shrink-0"/>
            <div className="flex-grow">
                <div className="rounded-md bg-slate-700/50 px-3 py-2">
                    <div className="flex items-center justify-between">
                        <span className="text-sm font-semibold text-white">{comment.user}</span>
                        <span className="text-xs text-slate-500">{new Date(comment.created).toLocaleDateString()}</span>
                    </div>
                    <p className="mt-1 text-sm text-slate-300">{comment.text}</p>
                </div>
                <div className="mt-1 flex items-center gap-4 pl-1">
                    <button onClick={handleLike} disabled={mutation.isPending}
                            className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-cyan-400">
                        <ThumbsUp size={14}/>
                        <span>{comment.likes_count}</span>
                    </button>
                    <button onClick={() => setIsReplying(!isReplying)}
                            className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-cyan-400">
                        <MessageSquare size={14}/>
                        <span>Ответить</span>
                    </button>
                </div>
                {isReplying && (
                    <div className="mt-2">
                        <AddCommentForm
                            reviewId={comment.review}
                            parentId={comment.id}
                            onSuccess={() => setIsReplying(false)}
                        />
                    </div>
                )}
            </div>
        </div>
    );
}