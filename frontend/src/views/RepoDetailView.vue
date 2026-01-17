      <div class="mb-6">
        <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-2">收藏</h2>
        <CollectionManager :repo-id="nameWithOwner />
      </div>

      <div class="mb-6">
        <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-2">我的笔记</h2>
        <NoteEditor :repo-id="nameWith_owner @update="handleNoteUpdate" />
      </div>

      <div class="mb-6">
        <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-2">标签</h2>
        <TagManager :repo_id="name_with_owner @update="handleTagUpdate" />
      </div>
