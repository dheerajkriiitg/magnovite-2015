/* global require */

var gulp = require('gulp');
var less = require('gulp-less');
var usemin = require('gulp-usemin');
var uglify = require('gulp-uglify');
var minifyCss = require('gulp-minify-css');
var rev = require('gulp-rev');
var clean = require('gulp-clean');
var runSequence = require('run-sequence');
var autoprefixer = require('gulp-autoprefixer');

gulp.task('watch', function() {
    'use strict';

    gulp.watch('app/static/css/**/*.less', ['css']);
});

/**
 * Distribute task, builds the whole project
 */
gulp.task('dist', function(cb) {
    'use strict';

    runSequence(['clean', 'usemin', 'css'], 'move-usemin', ['clean-usemin', 'prefix']);
});

/**
 * Builds the css files (less) to the app.css file
 */
gulp.task('css', function() {
    'use strict';

    return gulp.src('app/static/css/app.less')
               .pipe(less())
               .pipe(gulp.dest('app/static/css/'));
});

/**
 * CSS Prefix for the generated css file
 */
gulp.task('prefix', function() {
    'use strict';

    return gulp.src('app/static/dist/*.css', {base: './'})
               .pipe(autoprefixer({
                    cascade: false
               }))
               .pipe(gulp.dest('./'));
});

/**
 * Concats and builds the html
 */
gulp.task('usemin', function() {
    'use strict';

    return gulp.src('app/main/templates/*.html')
        .pipe(usemin({
            css: [minifyCss(), rev()],
            js: [uglify(), rev()]
        }))
        .pipe(gulp.dest('app/main/templates/tmp'));
});

/**
 * Moves the files generated by usemin to the
 * correct folder
 */
gulp.task('move-usemin', function() {
    'use strict';

    // move templates
    gulp.src('app/main/templates/tmp/*.html', {base: 'app/main/templates/tmp/'})
        .pipe(gulp.dest('app/main/templates/dist'));

    // move css files
    var files = [
        'app/main/templates/tmp/static/dist/*.css',
        'app/main/templates/tmp/static/dist/*.js'
    ];

    return gulp.src(files, {base: 'app/main/templates/tmp/static/'})
        .pipe(gulp.dest('app/static/'));

});

/**
 * Cleans the extra files created by usemin
 * after they are moved
 */
gulp.task('clean-usemin', function() {
    'use strict';

    return gulp.src('app/main/templates/tmp', {read: false})
    .pipe(clean());
});

/**
 * Cleans all files created by dist
 */
gulp.task('clean', function() {
    'use strict';

    var dirs = [
        'app/main/templates/tmp',
        'app/main/templates/dist',
        'app/static/dist'
    ];

    return gulp.src(dirs, {read: false})
        .pipe(clean());
});
