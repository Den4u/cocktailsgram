import styles from './style.module.css'
import { Container, LinkComponent } from '../index'

const Footer = () => {
  return <footer className={styles.footer}>
      <Container className={styles.footer__container}>
        <LinkComponent href='https://cocktailsgram.ddns.net/recipes' title='© 2024 CocktailsGram' className={styles.footer__brand} />
      </Container>
  </footer>
}

export default Footer
