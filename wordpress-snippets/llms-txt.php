<?php
/**
 * jaylog llms.txt — 답변엔진(LLM)용 사이트 요약을 https://jaylog.co.kr/llms.txt 로 제공.
 * Orca의 llms.txt 개념을 워드프레스에 이식한 것. sitemap이 "URL이 어디 있나"를 알려준다면
 * llms.txt는 "이 사이트가 무엇이고 어떤 글이 있나"를 LLM에게 알려준다(HTML 파싱 불필요).
 *
 * ▶ 설치 방법 (한 번만):
 *   워드프레스 관리자 → WPCode → Add Snippet → "Add Your Custom Code (New Snippet)"
 *   → Code Type: PHP Snippet → 아래 <?php 이후 내용을 붙여넣기
 *   → Insertion: Auto Insert / Run Everywhere → Save & Activate.
 *   (functions.php에 직접 넣어도 됨. 파일 접근이 되면 wp-content/mu-plugins/llms-txt.php 로 두는 게 가장 안전.)
 *
 * 설치 후 https://jaylog.co.kr/llms.txt 접속 → 발행글 목록이 text/plain으로 나오면 성공.
 * 발행글이 늘면 자동 반영된다(캐시 12시간).
 */

add_action('init', function () {
    // /llms.txt 요청만 가로챈다.
    $uri = parse_url($_SERVER['REQUEST_URI'] ?? '', PHP_URL_PATH);
    if (rtrim($uri, '/') !== '/llms.txt') {
        return;
    }

    header('Content-Type: text/plain; charset=utf-8');
    header('X-Robots-Tag: noindex');

    // 12시간 캐시 (발행글이 바뀌면 트랜지언트 만료 후 갱신)
    $cached = get_transient('jaylog_llms_txt');
    if ($cached !== false) {
        echo $cached;
        exit;
    }

    $site  = get_bloginfo('name');
    $desc  = get_bloginfo('description');
    $out   = "# {$site}\n\n";
    $out  .= "> {$desc}\n";
    $out  .= "> 해외직구·수입 통관 정보 블로그. 관세·면세기준(150달러, 미국 200달러)·통관 절차·품목별 규정을 50대 독자 눈높이로 다룹니다.\n\n";
    $out  .= "## 글 목록\n\n";

    $q = new WP_Query([
        'post_type'      => 'post',
        'post_status'    => 'publish',
        'posts_per_page' => 200,
        'orderby'        => 'date',
        'order'          => 'DESC',
        'no_found_rows'  => true,
    ]);
    foreach ($q->posts as $p) {
        $title = wp_strip_all_tags(get_the_title($p));
        $link  = get_permalink($p);
        // 설명: 발췌문(없으면 본문 앞부분)에서 한 줄 요약
        $ex = has_excerpt($p) ? get_the_excerpt($p) : wp_trim_words(wp_strip_all_tags($p->post_content), 30, '');
        $ex = trim(preg_replace('/\s+/', ' ', $ex));
        $out .= "- [{$title}]({$link}): {$ex}\n";
    }
    wp_reset_postdata();

    set_transient('jaylog_llms_txt', $out, 12 * HOUR_IN_SECONDS);
    echo $out;
    exit;
});
