require 'json'

module Jekyll
  class SeniorPageGenerator < Generator
    safe true
    priority :normal

    def generate(site)
      items = load_json(site, '_rawdata/senior.json')

      Jekyll.logger.info "SeniorGenerator:", "#{items.size}개 경로당/마을회관 페이지 생성 중..."
      items.each do |c|
        next if c['slug'].to_s.strip.empty?
        site.pages << SeniorPage.new(site, c)
      end

      Jekyll.logger.info "SeniorGenerator:", "완료 (#{items.size}개)"
    end

    private

    def load_json(site, path)
      file = File.join(site.source, path)
      return [] unless File.exist?(file)
      JSON.parse(File.read(file, encoding: 'utf-8'))
    rescue => e
      Jekyll.logger.warn "SeniorGenerator:", "#{path} 로드 실패: #{e.message}"
      []
    end
  end

  class SeniorPage < Page
    def initialize(site, c)
      @site = site
      @base = site.source
      @dir  = "center/#{c['slug']}"
      @name = 'index.html'

      self.process(@name)
      self.read_yaml(File.join(@base, '_layouts'), 'center.html')
      self.data.merge!(c)
      self.data['layout']      = 'center'
      self.data['title']       = build_title(c)
      self.data['description'] = build_desc(c)
    end

    private

    def build_title(c)
      loc = [c['doShort'], c['sigungu']].compact.join(' ')
      "#{c['centerName']} #{loc} 위치 전화번호"
    end

    def build_desc(c)
      loc = [c['doShort'], c['sigungu']].compact.join(' ')
      "#{loc} #{c['centerName']}(#{c['type']})의 위치, 전화번호, 관리기관 정보를 확인하세요."[0, 155]
    end
  end
end
