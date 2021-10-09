from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField("Заголовок", max_length=200)
    description = models.TextField("Описание группы")
    slug = models.SlugField("Уникальный адрес группы",
                            max_length=50, unique=True, default='')

    def __str__(self):
        return f"{self.title}"


class Post(models.Model):
    text = models.TextField(
        'Текст поста',
        help_text='Введите текст поста'
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
    )
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name="posts"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
        verbose_name='Группа',
        help_text='Выберите группу'
    )
    # Поле для картинки (необязательное) 
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        null=True,
        blank=True,
    )  
    # Аргумент upload_to указывает директорию, 
    # в которую будут загружаться пользовательские файлы. 

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:15] 


class Comment(models.Model):
    text = models.TextField(
        'Ваш комментарий',
    )
    post = models.ForeignKey(
        Post, 
        on_delete=models.CASCADE, 
        related_name='comments')
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name="comments"
    )
    
    created = models.DateTimeField(
        'Дата комментария',
        auto_now_add=True
    )


    class Meta:
        ordering = ('-created',)
        verbose_name = 'Коммент'
        verbose_name_plural = 'Комменты'

    def __str__(self):
        return self.text[:15] 


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following"
    )

    def __str__(self):
        return f"{self.title}"